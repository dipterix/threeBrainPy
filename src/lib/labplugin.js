import {BrainWidgetModel, BrainWidgetView, version} from './index';
import {IJupyterWidgetRegistry} from '@jupyter-widgets/base';

export const brainWidgetPlugin = {
  id: 'threebrainpy:plugin',
  requires: [IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'threebrainpy',
          version: version,
          exports: { BrainWidgetModel, BrainWidgetView }
      });
  },
  autoStart: true
};

export default brainWidgetPlugin;
