import { harnessConfig } from './nightengine/python/src/nightengine/web/harness/config.mjs';

// `just check web` builds the offline web build first. The engine's checks run, then Queen's.
export default harnessConfig({build: 'dist/web-offline', gameTests: 'tests/browser'});
