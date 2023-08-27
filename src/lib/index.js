// Export widget models and views, and the npm package version number.

import packageInfo from '../../package.json';

export {BrainWidgetView, BrainWidgetModel} from './widget';

const version = packageInfo.version;
export {version};
