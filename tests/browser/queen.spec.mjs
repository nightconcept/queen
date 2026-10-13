// Queen in Chromium with real touch at phone size: start a run, read the story, and play a card by dragging it.
import { test, expect } from '@playwright/test';
import { launch, point, python, tap, touch } from '../../nightengine/python/src/nightengine/web/harness/harness.mjs';

const NEW_RUN = [160, 506];  // queen/scenes/title.py: the first button with no saved run.
const CONTINUE = [160, 670];  // layout.bottom_buttons(1).

test('title, story, map and a dragged card in battle', async ({page}) => {
  const errors = await launch(page);
  await tap(page, ...NEW_RUN);
  await expect.poll(() => python(page, 'type(app.game.scene).__name__')).toBe('StoryScene');
  // Three cards (intro, agenda, act): finish the typing, then Continue, until the map shows.
  for (let i = 0; i < 12 && await python(page, 'type(app.game.scene).__name__') !== 'Explore'; i++) {
    await tap(page, 160, 300);
    await page.waitForTimeout(250);
    await tap(page, ...CONTINUE);
    await page.waitForTimeout(250);
  }
  await expect.poll(() => python(page, 'type(app.game.scene).__name__')).toBe('Explore');
  await page.screenshot({path: 'test-results/queen-map.png'});

  // Start a fight with one Drone, then drag a Fire card onto it.
  await python(page, `g = app.game
g.run.loc().enemies = ["DRONE"]
g.run.steps.insert(0, {"kind": "battle", "enemies": ["DRONE"], "location": g.run.location, "boss": False})`);
  await expect.poll(() => python(page, 'type(app.game.scene).__name__')).toBe('BattleScene');
  await expect.poll(() => python(page, 'app.game.scene.busy'), {timeout: 20000}).toBe(false);
  const card = await python(page, `s = app.game.scene
b = s.battle
i = next(i for i, c in enumerate(b.hand) if c.card.target == "enemy" or c.card.type == "action")
sl = s.slots[b.hand[i].uid]
x, y = s.fighter_xy(b.foes[0].uid)
[int(sl.x), int(sl.y), int(x), int(y), len(b.hand)]`);
  const cdp = await page.context().newCDPSession(page);
  const [cx, cy, ex, ey, n] = card;
  const steps = 10;
  await touch(cdp, 'touchStart', [{...(await point(page, cx, cy)), id: 1}]);
  for (let i = 1; i <= steps; i++) {
    const p = await point(page, cx + (ex - cx) * i / steps, cy + (ey - cy) * i / steps);
    await touch(cdp, 'touchMove', [{...p, id: 1}]);
    await page.waitForTimeout(20);
  }
  await touch(cdp, 'touchEnd', []);
  await expect.poll(() => python(page, 'len(app.game.scene.battle.hand)')).toBe(n - 1);
  await page.waitForTimeout(800);
  await page.screenshot({path: 'test-results/queen-battle.png'});
  expect(errors).toEqual([]);
});
