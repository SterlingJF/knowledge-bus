export interface Lane {
  readonly titles: readonly string[];
  readonly workersMayContend: boolean;
}

export const testsObservedToFailWhileWorkersContend: readonly string[] = [
  'a hidden connection takes no pointer, and a centreline click lands on whatever is visible there',
];

export const testsObservedToPassWhileWorkersContend: readonly string[] = [
  'opens offline on composition counts, and the lines that tell required from optional are one menu step away',
  'the universe overview opens from the title and reports its counts',
  'cards carry ordering icons, cardinality and referenced-frame icons',
  'selection frames the subject beside the overlay and dismissal returns to the overview',
  'dismissing the detail returns the camera to the same overview the map fits to',
  'previewing a card while another is selected keeps it dimmed and only recolours its border',
  'detail sections navigate, lists disclose after three, and inline references move the selection',
  'composition copy states each requirement once over its group, with its conditions',
  'the connection panel states its reading in the panel, not only in a tooltip',
  'the source definition is a code block with a control that copies it',
  'the connection panel carries the same gating condition as the entity panel',
  'relations read with their authored phrasing, never a raw kind',
  'view options are persistent, independent of selection, and reset keeps the selection',
  'frame filters narrow the map and the active dot reflects them',
  'composition line style marks required and situational memberships',
  'every view lays out, and the artifact view rolls connections up',
  'a connection opens its own details listing every source',
  'search reveals an element, switching view when it is not on the map',
  'blank canvas clears the selection and Escape only dismisses the detail',
  'the minimap toggles, drags by its header, and navigates by its plot',
  'the dock zooms, fits, and reports the zoom level',
  'theme switching drives the whole surface',
  'the export menu offers SVG and downloads a complete dual-theme file',
  'the export is deterministic, complete and free of chrome',
  'tokens reach live consumers including an open overlay',
  'narrow viewports stack the overlay and keep every control reachable',
  'reduced motion makes camera changes immediate',
  'library: two viewers stay independent, destroy cleans up, and bad input refuses',
  'P19 two model concepts draw two marks, in a universe whose vocabulary the curated glyphs have never seen',
  'a selected connection keeps every card count on the map',
  'edge labels appear only for the selected set, read as authored phrasing, and name both ends',
  'the detail overlay is named for definitions and never repeats the entity kind',
  'the map control names the action its next press performs',
  'view options carry no theme control and the theme button shows the current theme',
  'the chrome uses the board glyphs for its menu and its title',
  'a part draws its token value at and above 100% and grows to its limit as you zoom out',
  "a connection label's box is never smaller than the text it draws, at any zoom",
  'a connection label is a plate edged by its declared border, in both themes',
  'a connection label keeps its shape as the camera zooms',
  'counts follow the emphasis model: a hover hides none of them, and a count a selection hides is unreachable',
  'an idle board draws every card at rest and every connection at idle strength',
  'hovering a card lights its connections and hushes the rest of the board, without claiming to be selected',
  'P17 every property a hover moves, on everything the emphasis touches, is one that element eases: a card hovered over lines',
  'P17 every property a hover moves, on everything the emphasis touches, is one that element eases: a card hovered over counts',
  'P17 every property a hover moves, on everything the emphasis touches, is one that element eases: a labelled connection of the selected card hovered',
  'with reduced motion nothing the emphasis touches takes any time to change: a card hovered over lines',
  'with reduced motion nothing the emphasis touches takes any time to change: a card hovered over counts',
  'with reduced motion nothing the emphasis touches takes any time to change: a labelled connection of the selected card hovered',
  'selecting a card hides the connections that are not its own',
  'hovering one connection of the selected card lights it and rests its siblings',
  'an emphasised connection holds full strength on an idle board and gives it up inside a selection',
  'P14 the pointer on a drawn centreline meets a hit path, never a painted mark: composition lines, idle',
  'P14 the pointer on a drawn centreline meets a hit path, never a painted mark: composition lines, Decision brief selected',
  'P14 the pointer on a drawn centreline meets a hit path, never a painted mark: relation lines, idle',
  'P14 the pointer on a drawn centreline meets a hit path, never a painted mark: component: offset and inline connection handles',
  "a click on the drawn centreline of a selected card's own connection selects that connection",
  'P18 canonical product-development: selected composition labels avoid cards and each other through dock steps',
  "P16 the pointer on a connection's label lights that connection and only that one",
  'the hover holds while the pointer moves from a lit wire onto its own label, and back',
  'P13 the boundary ground swallows no count badge and no drawn wire that is painted without it',
  'a ground painted on the boundary itself is reported swallowing the badges and wires beneath it',
  'P15 a dimmed card paints the ground it stands on, so no board dot shows through it and it is no hole in a grounded boundary: grouped elements',
  'P15 a dimmed card paints the ground it stands on, so no board dot shows through it and it is no hole in a grounded boundary: flat elements',
  'P15 a dimmed card paints the ground it stands on, so no board dot shows through it and it is no hole in a grounded boundary: artifacts',
  'P15 a dimmed card paints the ground it stands on, so no board dot shows through it and it is no hole in a grounded boundary: frames',
  'a transparent dimmed card is reported showing the dots, and one painted the canvas is reported a hole in its ground',
  'chrome that floats over the map is a lifted surface; a card at rest is not',
  'P21 every claim the guidance document makes reaches its own subject verbatim, and the copy explorer writes around it is never a guidance kind id',
  'card titles and subtitles grow toward true size without their ink leaving the card or reaching the frame-icon row',
  'a card mark stands clear of the title it introduces',
  'a frame or frame-option description is drawn within its line allowance, and carries its full text exactly where it is clipped',
  'frame and frame-option panels keep every authored row meaning with its own static row',
  'frame options are complete static values while long element groups disclose once',
  'semantic rows remain quiet, whole and reachable in capped desktop and narrow panels',
  'the detail panel stands beside the subject it describes, on screen and clear of the dock',
  'a panel group is drawn by a border and never by a fill, in both themes, with the guidance disclosure above the composition it qualifies',
];

export const LANES = {
  parallel: { titles: testsObservedToPassWhileWorkersContend, workersMayContend: true },
  exclusive: { titles: testsObservedToFailWhileWorkersContend, workersMayContend: false },
} as const satisfies Record<string, Lane>;

export type LaneName = keyof typeof LANES;

export const LANE_NAMES = Object.keys(LANES) as LaneName[];

export const everyTitleALaneClaims = (): string[] => LANE_NAMES.flatMap((name) => [...LANES[name].titles]);

const MATCHING_NOTHING = /(?!)/;

const escapedForRegExp = (title: string): string => title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const titlesEndingTheGrepTarget = (titles: readonly string[]): RegExp =>
  titles.length ? new RegExp(titles.map((t) => `${escapedForRegExp(t)}$`).join('|')) : MATCHING_NOTHING;

export const laneOptions = (lane: Lane) =>
  lane.workersMayContend
    ? { grepInvert: titlesEndingTheGrepTarget(LANES.exclusive.titles), workers: '50%' as const, fullyParallel: true }
    : { grep: titlesEndingTheGrepTarget(LANES.exclusive.titles), workers: 1, fullyParallel: false };

export const laneNamed = (name: string | undefined): Lane => {
  if (!name || !LANE_NAMES.includes(name as LaneName))
    throw new Error(`set KB_EXPLORER_LANE to one of ${LANE_NAMES.join(', ')}; it was ${name ?? 'unset'}`);
  return LANES[name as LaneName];
};
