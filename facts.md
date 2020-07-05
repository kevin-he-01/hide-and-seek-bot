# Useful facts
- Vision (See https://github.com/acmucsd/hide-and-seek-ai/blob/f06770a423b0602df8a6393e0c470c2027bc54a5/src/Map/index.ts)
    - vision range = sqrt(48), inclusive, aka. r = [0, sqrt(48)]
    - quoting from it:
    ```typescript
    export const defaultMatchConfigs: HideAndSeekConfigs = {
      liveView: true,
      delay: 0.2,
      roundLimit: 200,
      seed: 0,
      replayDirectory: './replays',
      mode: GameModes.tag,
      randomizeSeeker: true,
      storeReplay: true,
      parameters: {
        VISION_RANGE: 48,
        DENSITY: 0.35,
        SEEKER_MAX: 3,
        MIN_HEIGHT: 16,
        MIN_WIDTH: 16,
        MAX_HEIGHT: 24,
        MAX_WIDTH: 24
      }
    }
    ```

- Constants
    - Max number of units on a team: 3
    - either horizontal or vertical symmetry
    - generated using game of life (GOL) rules
- ID assignment
    - each seeker will have a corresponding hider spawned at the opposite end of the line of symmetry with id = self.id + 1
        - See https://github.com/acmucsd/hide-and-seek-ai/blob/f06770a423b0602df8a6393e0c470c2027bc54a5/src/Map/gen.ts#L27
    - IDs [always start from 4](https://github.com/acmucsd/hide-and-seek-ai/blob/f06770a423b0602df8a6393e0c470c2027bc54a5/src/Map/index.ts#L17)
        - `public gameID: number = 4;`
    - Therefore
        - 4: Seeker 1
        - 5: Hider 1
        - 6: Seeker 2
        - 7: Hider 2
        - 8: Seeker 3
        - 9: Hider 3
        - even: seeker
        - odd: hider