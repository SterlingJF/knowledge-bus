import test from 'node:test';
import assert from 'node:assert/strict';
import { type CardEmphasis, type EdgeEmphasis, emphasise } from '@/src/lib/emphasis';
import { type DisplayEdge, type Selection, type ViewOptions, emptySelection, initialOptions, updateOptions } from '@/src/lib/model';
import { type Scene } from '@/src/lib/scene';
import { renderStates, sceneFor, type RenderState } from './render-states';

interface Row {
  subject: string;
  itself: CardEmphasis | null;
  itsCards: CardEmphasis;
  otherCards: CardEmphasis;
  itsEdges: EdgeEmphasis | null;
  otherEdges: EdgeEmphasis;
  itsNub: EdgeEmphasis | null;
  itsCardsNubs: EdgeEmphasis;
  otherNubs: EdgeEmphasis;
  hoveredEdge?: EdgeEmphasis;
  previewsItself?: true;
  within?: string;
}

const TABLE: Row[] = [
  {
    subject: 'none',
    itself: null,
    itsCards: 'idle',
    otherCards: 'idle',
    itsEdges: null,
    otherEdges: 'rest',
    itsNub: null,
    itsCardsNubs: 'active',
    otherNubs: 'active',
  },
  {
    subject: 'hovered card',
    itself: 'idle',
    itsCards: 'idle',
    otherCards: 'hushed',
    itsEdges: 'active',
    otherEdges: 'rest',
    itsNub: 'active',
    itsCardsNubs: 'rest',
    otherNubs: 'rest',
    previewsItself: true,
  },
  {
    subject: 'selected card',
    itself: 'active',
    itsCards: 'idle',
    otherCards: 'dimmed',
    itsEdges: 'active',
    otherEdges: 'hidden',
    itsNub: 'active',
    itsCardsNubs: 'rest',
    otherNubs: 'hidden',
  },
  {
    subject: 'hovered connection',
    itself: null,
    itsCards: 'idle',
    otherCards: 'hushed',
    itsEdges: null,
    otherEdges: 'rest',
    itsNub: null,
    itsCardsNubs: 'rest',
    otherNubs: 'rest',
  },
  {
    subject: 'selected connection',
    itself: null,
    itsCards: 'idle',
    otherCards: 'dimmed',
    itsEdges: null,
    otherEdges: 'hidden',
    itsNub: null,
    itsCardsNubs: 'rest',
    otherNubs: 'hidden',
  },
  {
    subject: 'hovered edge of the selected card',
    itself: 'active',
    itsCards: 'idle',
    otherCards: 'dimmed',
    itsEdges: 'rest',
    otherEdges: 'hidden',
    itsNub: 'active',
    itsCardsNubs: 'rest',
    otherNubs: 'hidden',
    hoveredEdge: 'active',
    within: 'selected card',
  },
];

const connected = renderStates().filter(
  (state) =>
    state.options.view !== 'frames' && state.options.connections && state.selection.entity === '' && state.selection.connection === '',
);

const touches = (edge: { from: string; to: string; targetPair?: string[] }, id: string) =>
  edge.from === id || edge.to === id || edge.targetPair?.includes(id) === true;

function actAs(row: Row, scene: Scene): { selection: Selection; hover: string; subject: string; kin: Set<string> } | null {
  const edge = scene.edges[0];
  const card = edge?.from ?? scene.layout.cards[0]?.id;
  if (row.subject !== 'none' && (!edge || !card)) return null;
  const kin = new Set<string>();
  if (row.subject.endsWith('connection')) for (const id of [edge.from, edge.to, ...(edge.targetPair ?? [])]) kin.add(id);
  if (row.subject.endsWith('card')) {
    kin.add(card);
    for (const other of scene.edges)
      if (touches(other, card) && (row.subject !== 'hovered card' || !onlyADistinction(other)))
        for (const id of [other.from, other.to, ...(other.targetPair ?? [])]) kin.add(id);
  }
  const pick = {
    none: { selection: emptySelection(), hover: '', subject: '' },
    'hovered card': { selection: emptySelection(), hover: card, subject: card },
    'selected card': { selection: { entity: card, connection: '', option: '' }, hover: '', subject: card },
    'hovered connection': { selection: emptySelection(), hover: edge?.path ?? '', subject: edge?.path ?? '' },
    'selected connection': { selection: { entity: '', connection: edge?.path ?? '', option: '' }, hover: '', subject: edge?.path ?? '' },
    'hovered edge of the selected card': { selection: { entity: card, connection: '', option: '' }, hover: '', subject: card },
  }[row.subject]!;
  return { ...pick, kin };
}

test('E1 emphasis follows the declared table in every state that draws connections', () => {
  const failures: string[] = [];
  const rowsCompared = new Set<string>();
  const statesCompared = new Set<string>();
  assert.notEqual(connected.length, 0, 'the enumeration must supply states that draw connections');
  for (const state of connected) {
    const base = sceneFor(state);
    for (const row of TABLE) {
      const act = actAs(row, base);
      if (!act) continue;
      const scene =
        act.selection.entity || act.selection.connection
          ? sceneFor({
              ...state,
              name: `${state.name}/${act.selection.entity}${act.selection.connection}`,
              selection: act.selection,
            } as RenderState)
          : base;
      const hovered = row.hoveredEdge ? (scene.edges.find((e) => touches(e, act.subject))?.path ?? '') : act.hover;
      const shown = emphasise(scene, act.selection, hovered);
      const note = (what: string) => failures.push(`${state.name} · ${row.subject}: ${what}`);
      const compare = (got: string | undefined, want: string, what: string) => {
        rowsCompared.add(row.subject);
        statesCompared.add(state.name);
        if (got !== want) note(`${what} is ${got}, expected ${want}`);
      };
      if (row.hoveredEdge && !hovered) note(`no edge of ${act.subject} is available to hover`);
      compare(shown.preview, row.previewsItself ? act.subject : '', 'the previewed card');
      for (const card of scene.layout.cards) {
        const want =
          card.id === act.subject && row.itself
            ? row.itself
            : act.kin.size === 0
              ? 'idle'
              : act.kin.has(card.id)
                ? row.itsCards
                : row.otherCards;
        compare(shown.cards.get(card.id), want, `card ${card.id}`);
      }
      for (const edge of scene.edges) {
        const mine = row.subject.endsWith('connection') ? edge.path === act.subject : touches(edge, act.subject);
        const asked = row.subject.endsWith('connection') ? edge.path === act.subject : !!act.selection.entity && mine;
        const want =
          state.options.connections === 'relations' && onlyADistinction(edge) && !asked
            ? 'hidden'
            : !act.subject
              ? row.otherEdges
              : row.hoveredEdge && edge.path === hovered
                ? row.hoveredEdge
                : mine
                  ? (row.itsEdges ?? 'active')
                  : row.otherEdges;
        compare(shown.edges.get(edge.path), want, `edge ${edge.path}`);
      }
      for (const nub of scene.nubs) {
        const want =
          nub.id === act.subject && row.itsNub
            ? row.itsNub
            : act.kin.size === 0
              ? 'active'
              : act.kin.has(nub.id)
                ? row.itsCardsNubs
                : row.otherNubs;
        compare(shown.nubs.get(nub.id), want, `nub ${nub.id}`);
      }
    }
  }
  assert.deepEqual(failures.slice(0, 6), []);
  assert.deepEqual(
    TABLE.map((row) => row.subject).filter((subject) => !rowsCompared.has(subject)),
    [],
    'every declared row must be compared in at least one state',
  );
  assert.deepEqual(
    connected.map((state) => state.name).filter((name) => !statesCompared.has(name)),
    [],
    'every state that draws connections must contribute at least one comparison',
  );
});

const CELLS = ['itself', 'itsCards', 'otherCards', 'itsEdges', 'otherEdges', 'itsNub', 'itsCardsNubs', 'otherNubs', 'hoveredEdge'] as const;
const LOUD: (CardEmphasis | EdgeEmphasis)[] = ['hidden', 'dimmed'];
const isAHover = (row: Row) => row.subject.startsWith('hovered ');
const cellsOf = (row: Row) => CELLS.map((cell) => row[cell] ?? null);

function hoverRowsLouderThanAGlance(table: Row[]): string[] {
  const broken: string[] = [];
  for (const row of table.filter(isAHover)) {
    const settledBeneath = table.find((other) => other.subject === (row.within ?? 'none'));
    if (!settledBeneath) {
      broken.push(`${row.subject}: happens within ${row.within}, which the table does not declare`);
      continue;
    }
    for (const cell of CELLS) {
      const mine = row[cell];
      if (mine && LOUD.includes(mine) && settledBeneath[cell] !== mine)
        broken.push(`${row.subject}: ${cell} is ${mine}, which ${settledBeneath.subject} beneath it is not`);
    }
    if (row.itself === 'active' && settledBeneath.itself !== 'active') broken.push(`${row.subject}: claims to be selected`);
    const twin = table.find((other) => other.subject === row.subject.replace('hovered ', 'selected '));
    if (twin && JSON.stringify(cellsOf(twin)) === JSON.stringify(cellsOf(row)))
      broken.push(`${row.subject}: reads exactly as ${twin.subject}`);
  }
  return broken;
}

test('E3 a hover only hushes: it hides and dims nothing its settled state does not, never claims selection, and never equals its selected twin', () => {
  const hovers = TABLE.filter(isAHover);
  const twinned = hovers.filter((row) => TABLE.some((other) => other.subject === row.subject.replace('hovered ', 'selected ')));
  assert.notEqual(hovers.length, 0, 'the table must declare hover rows');
  assert.notEqual(twinned.length, 0, 'some hover row must have a selected twin to differ from');
  assert.deepEqual(hoverRowsLouderThanAGlance(TABLE), []);
  const remerged = TABLE.map((row) =>
    isAHover(row) && !row.within
      ? { ...TABLE.find((other) => other.subject === row.subject.replace('hovered ', 'selected '))!, subject: row.subject }
      : row,
  );
  assert.notDeepEqual(hoverRowsLouderThanAGlance(remerged), [], 'a hover row re-merged with its selected twin must be reported');
});

test('E2 exactly one subject wins, in the declared order', () => {
  const state = connected[0];
  const scene = sceneFor(state);
  const edge = scene.edges[0];
  const stranger = scene.layout.cards.find((c) => !touches(edge, c.id))!.id;

  const selectionOverHover = emphasise(scene, { entity: edge.from, connection: '', option: '' }, stranger);
  assert.equal(selectionOverHover.cards.get(edge.from), 'active', 'a selected card outranks a hovered card');
  assert.equal(selectionOverHover.preview, stranger, 'the hovered card previews instead of taking over');

  const cardSelectionOverEdgeHover = emphasise(scene, { entity: stranger, connection: '', option: '' }, edge.path);
  assert.equal(cardSelectionOverEdgeHover.cards.get(stranger), 'active', 'a selected card outranks a hovered connection');

  const edgeSelectionOverCardHover = emphasise(scene, { entity: '', connection: edge.path, option: '' }, stranger);
  assert.equal(edgeSelectionOverCardHover.edges.get(edge.path), 'active', 'a selected connection outranks a hovered card');
  assert.notEqual(edgeSelectionOverCardHover.cards.get(stranger), 'active');

  const edgeHoverOverCardHover = emphasise(scene, emptySelection(), edge.path);
  assert.equal(edgeHoverOverCardHover.edges.get(edge.path), 'active', 'a hovered connection is the subject, not its cards');
  assert.notEqual(edgeHoverOverCardHover.cards.get(edge.from), 'active');
});

const THE_KIND_THE_PROTOCOL_SAYS_MUST_NOT_BE_SUBSTITUTED = 'distinct-from';

const kindsCarried = (edge: DisplayEdge): string[] => (edge.members?.length ? edge.members.flatMap(kindsCarried) : [edge.kind ?? '']);

const onlyADistinction = (edge: DisplayEdge): boolean =>
  kindsCarried(edge).every((kind) => kind === THE_KIND_THE_PROTOCOL_SAYS_MUST_NOT_BE_SUBSTITUTED);

const relationBoard = (tag: string, patch: Partial<ViewOptions>, selection: Selection = emptySelection()): RenderState => ({
  name: `boundaries on demand · ${tag} · ${JSON.stringify(selection)}`,
  options: updateOptions(initialOptions(), { connections: 'relations', ...patch }),
  selection,
});

const RELATION_BOARDS: { tag: string; patch: Partial<ViewOptions> }[] = [
  { tag: 'artifacts lines', patch: { view: 'artifacts', display: 'lines' } },
  { tag: 'artifacts counts', patch: { view: 'artifacts', display: 'counts' } },
  { tag: 'grouped elements lines', patch: { view: 'elements', group: true, display: 'lines' } },
  { tag: 'grouped elements counts', patch: { view: 'elements', group: true, display: 'counts' } },
  { tag: 'flat elements lines', patch: { view: 'elements', group: false, display: 'lines' } },
];

const selecting = (entity: string): Selection => ({ entity, connection: '', option: '' });

test('V1 at rest no relation view shows a connection that only marks a distinction, and shows every other one', () => {
  for (const { tag, patch } of RELATION_BOARDS) {
    const scene = sceneFor(relationBoard(tag, patch));
    const distinctions = scene.edges.filter(onlyADistinction);
    assert.ok(distinctions.length > 0, `${tag}: the board must hold a distinction for this case to mean anything`);
    assert.ok(scene.edges.length > distinctions.length, `${tag}: the board must hold other relations too`);
    const shown = emphasise(scene, emptySelection(), '');
    assert.deepEqual(
      scene.edges.filter((edge) => (shown.edges.get(edge.path) === 'hidden') !== onlyADistinction(edge)).map((edge) => edge.path),
      [],
      `${tag}: exactly the distinctions are hidden`,
    );
    assert.deepEqual(
      [...new Set(scene.edges.filter((edge) => !onlyADistinction(edge)).map((edge) => shown.edges.get(edge.path)))],
      ['rest'],
    );
  }
});

test('V1 a pair of cards carrying a distinction beside another relation is still shown at rest', () => {
  const scene = sceneFor(relationBoard('artifacts lines', { view: 'artifacts', display: 'lines' }));
  const mixed = scene.edges.filter(
    (edge) => kindsCarried(edge).includes(THE_KIND_THE_PROTOCOL_SAYS_MUST_NOT_BE_SUBSTITUTED) && !onlyADistinction(edge),
  );
  assert.ok(mixed.length > 0, 'the artifacts board must collapse a distinction with another relation for this case to mean anything');
  const shown = emphasise(scene, emptySelection(), '');
  assert.deepEqual([...new Set(mixed.map((edge) => shown.edges.get(edge.path)))], ['rest']);
});

test('V2 selecting a card shows the distinctions that touch it with the selection treatment, and no other distinction', () => {
  for (const { tag, patch } of RELATION_BOARDS) {
    const rest = sceneFor(relationBoard(tag, patch));
    const card = rest.layout.cards.find((c) => rest.edges.some((edge) => onlyADistinction(edge) && touches(edge, c.id)))!.id;
    const selection = selecting(card);
    const scene = sceneFor(relationBoard(tag, patch, selection));
    const shown = emphasise(scene, selection, '');
    const own = scene.edges.filter((edge) => onlyADistinction(edge) && touches(edge, card));
    const far = scene.edges.filter((edge) => onlyADistinction(edge) && !touches(edge, card));
    assert.ok(own.length > 0, `${tag}: ${card} must touch a distinction`);
    assert.deepEqual([...new Set(own.map((edge) => shown.edges.get(edge.path)))], ['active'], `${tag}: ${card}'s own distinctions`);
    assert.deepEqual([...new Set(far.map((edge) => shown.edges.get(edge.path)))], far.length ? ['hidden'] : []);
    for (const edge of own)
      for (const end of [edge.from, edge.to]) assert.notEqual(shown.cards.get(end), 'dimmed', `${tag}: ${end} is kin of ${card}`);
  }
});

test('V3 a distinction rolled up onto the selected artifact is shown with the selection treatment', () => {
  const patch: Partial<ViewOptions> = { view: 'artifacts', display: 'lines' };
  const rest = sceneFor(relationBoard('artifacts lines', patch));
  const rolled = rest.edges.find((edge) => onlyADistinction(edge) && edge.paint === 'rolled');
  assert.ok(rolled, 'the artifacts board must roll a distinction up onto its artifacts for this case to mean anything');
  const selection = selecting(rolled.to);
  const scene = sceneFor(relationBoard('artifacts lines', patch, selection));
  assert.equal(emphasise(scene, selection, '').edges.get(rolled.path), 'active');
  assert.equal(
    emphasise(scene, selection, scene.edges.find((e) => e.path !== rolled.path && touches(e, rolled.to))?.path ?? '').edges.get(
      rolled.path,
    ),
    'rest',
  );
});

test('V4 the distinction chip shows every distinction at once, and a selection then hides only what it hides of any relation', () => {
  for (const { tag, patch } of RELATION_BOARDS) {
    const chipped = { ...patch, emphasis: [THE_KIND_THE_PROTOCOL_SAYS_MUST_NOT_BE_SUBSTITUTED] };
    const scene = sceneFor(relationBoard(`${tag} chipped`, chipped));
    const distinctions = scene.edges.filter(onlyADistinction);
    const shown = emphasise(scene, emptySelection(), '');
    assert.deepEqual([...new Set(distinctions.map((edge) => shown.edges.get(edge.path)))], ['rest'], tag);
    assert.ok(
      distinctions.every((edge) => edge.emphasized),
      `${tag}: the chip emphasises what it reveals`,
    );
    const card = scene.layout.cards.find((c) => scene.edges.some((edge) => !onlyADistinction(edge) && touches(edge, c.id)))!.id;
    const selection = selecting(card);
    const selected = sceneFor(relationBoard(`${tag} chipped`, chipped, selection));
    const settled = emphasise(selected, selection, '');
    for (const edge of selected.edges)
      assert.equal(settled.edges.get(edge.path), touches(edge, card) ? 'active' : 'hidden', `${tag}: ${edge.path}`);
  }
});

test('V5 a hovered card reveals no distinction, and a card it only distinguishes is not its kin', () => {
  const patch: Partial<ViewOptions> = { view: 'elements', group: true, display: 'lines' };
  const scene = sceneFor(relationBoard('grouped elements lines', patch));
  const card = scene.layout.cards.find((c) => {
    const distinguished = scene.edges.filter((edge) => onlyADistinction(edge) && touches(edge, c.id)).flatMap((e) => [e.from, e.to]);
    const related = new Set(scene.edges.filter((edge) => !onlyADistinction(edge) && touches(edge, c.id)).flatMap((e) => [e.from, e.to]));
    return distinguished.some((id) => id !== c.id && !related.has(id)) && related.size > 0;
  });
  assert.ok(card, 'the board must hold a card distinguished from one it has no other relation with');
  const shown = emphasise(scene, emptySelection(), card.id);
  const own = scene.edges.filter((edge) => onlyADistinction(edge) && touches(edge, card.id));
  assert.deepEqual([...new Set(own.map((edge) => shown.edges.get(edge.path)))], ['hidden']);
  const related = new Set(scene.edges.filter((edge) => !onlyADistinction(edge) && touches(edge, card.id)).flatMap((e) => [e.from, e.to]));
  for (const id of own.flatMap((edge) => [edge.from, edge.to]).filter((id) => id !== card.id && !related.has(id)))
    assert.equal(shown.cards.get(id), 'hushed', `${id} is only distinguished from ${card.id}`);
});

test('V6 showing distinctions on demand moves no route: every edge routes the same with the chip on as at rest', () => {
  for (const { tag, patch } of RELATION_BOARDS) {
    const rest = sceneFor(relationBoard(tag, patch));
    const chipped = sceneFor(relationBoard(`${tag} chipped`, { ...patch, emphasis: [THE_KIND_THE_PROTOCOL_SAYS_MUST_NOT_BE_SUBSTITUTED] }));
    assert.deepEqual(
      chipped.edges.map((edge) => [edge.path, edge.d, edge.drawn]),
      rest.edges.map((edge) => [edge.path, edge.d, edge.drawn]),
      tag,
    );
    assert.deepEqual(chipped.labels, rest.labels, tag);
    assert.deepEqual(chipped.nubs, rest.nubs, tag);
  }
});
