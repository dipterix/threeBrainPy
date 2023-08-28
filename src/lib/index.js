// Export widget models and views, and the npm package version number.

import packageInfo from '../../package.json';
const version = packageInfo.version;
import {BrainWidgetView, BrainWidgetModel} from './widget';

console.log(version);
export {BrainWidgetView, BrainWidgetModel, version};
