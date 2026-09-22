import test from 'node:test';
import assert from 'node:assert/strict';
import { type View, type ViewOptions, aViewGroupsItsElements, initialOptions, updateOptions } from '@/src/lib/model';

const LINE_STYLES = ['uniform', 'distinct'] as const;

test('turning the display from counts to lines lands on the distinct line style, whichever style the counted state carried', () => {
  const landings: string[] = [];
  for (const lineStyle of LINE_STYLES) {
    const counted = updateOptions(initialOptions(), { connections: 'composition', display: 'counts', lineStyle });
    const after = updateOptions(counted, { display: 'lines' });
    if (after.lineStyle !== 'distinct') landings.push(`counts/${lineStyle} turned to lines and landed on ${after.lineStyle}`);
  }
  assert.deepEqual(landings, []);
});

test('a line style already on show survives, so the rule states the landing of a turn rather than overriding a choice', () => {
  const counted = updateOptions(initialOptions(), { connections: 'composition', display: 'counts', lineStyle: 'distinct' });
  assert.equal(updateOptions(counted, { display: 'lines', lineStyle: 'uniform' }).lineStyle, 'uniform');
  const uniform = updateOptions(initialOptions(), { connections: 'composition', display: 'lines', lineStyle: 'uniform' });
  assert.equal(updateOptions(uniform, { display: 'lines' }).lineStyle, 'uniform');
  assert.equal(updateOptions(uniform, { frames: [] }).lineStyle, 'uniform');
});

const CONTROLS_THE_VIEW_OFFERS: Record<View, Partial<ViewOptions> & { groups: boolean }> = {
  frames: { groups: false },
  artifacts: { connections: 'composition', display: 'lines', lineStyle: 'distinct', groups: false },
  elements: { connections: 'composition', display: 'counts', lineStyle: 'distinct', group: true, groups: true },
};

test('each view opens on its own defaults, and only the view that draws elements offers a grouping control', () => {
  const wrong: string[] = [];
  for (const [view, expected] of Object.entries(CONTROLS_THE_VIEW_OFFERS) as [View, (typeof CONTROLS_THE_VIEW_OFFERS)[View]][]) {
    const opened = initialOptions(view);
    assert.equal(opened.view, view, `initialOptions(${view}) opens on ${view}`);
    for (const [key, value] of Object.entries(expected))
      if (key !== 'groups' && opened[key as keyof ViewOptions] !== value)
        wrong.push(`${view} opens with ${key} ${String(opened[key as keyof ViewOptions])} rather than ${String(value)}`);
    if (aViewGroupsItsElements(view) !== expected.groups)
      wrong.push(`${view} ${aViewGroupsItsElements(view) ? 'offers' : 'withholds'} a grouping control against the brief`);
  }
  assert.deepEqual(wrong, []);
});
