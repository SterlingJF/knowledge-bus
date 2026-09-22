import test from 'node:test';
import assert from 'node:assert/strict';
import { type CardEmphasis, type EdgeEmphasis, emphasise } from '@/src/lib/emphasis';
import { type Selection, emptySelection } from '@/src/lib/model';
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
      if (touches(other, card)) for (const id of [other.from, other.to, ...(other.targetPair ?? [])]) kin.add(id);
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
        const want = !act.subject
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
