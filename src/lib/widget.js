import { DOMWidgetModel, DOMWidgetView } from '@jupyter-widgets/base';
import {
  ViewerApp, ViewerWrapper, StorageCache, Readers, 
  Constants, Drivers, ExternLibs
} from '@rave-ieeg/three-brain/src/js/index.js';


const global_cache = window.global_cache || new StorageCache();
window.global_cache = global_cache;
window.THREE = ExternLibs.THREE;

// See example.py for the kernel counterpart to this file.

// Custom Model. Custom widgets models must at least provide default values
// for model attributes, including
//
//  - `_view_name`
//  - `_view_module`
//  - `_view_module_version`
//
//  - `_model_name`
//  - `_model_module`
//  - `_model_module_version`
//
//  when different from the base class.

// When serialiazing the entire widget state for embedding, only values that
// differ from the defaults will be serialized.

export class BrainWidgetModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name : 'BrainWidgetModel',
      _view_name : 'BrainWidgetView',
      _model_module : 'threebrainpy',
      _view_module : 'threebrainpy',
      _model_module_version : '0.1.0',
      _view_module_version : '0.1.0',
      config : null
    };
  }
}

export class BrainWidgetView extends DOMWidgetView {

  render() {
    window.www = this;
    this.value_changed();
    // Observe and act on future changes to the value attribute
    this.model.on('change:config', this.value_changed, this);
    window.addEventListener('resize', this.resize.bind(this));
  }

  value_changed() {
    if( !this.model ) return;
    let data = this.model.get('config');
    if (typeof data !== 'string' || data.trim() === "" ) return;
    data = JSON.parse(data); 
    if (!data ) return;

    try {
      let width = data.width ?? 1024;
      if ( width <= 1.1 ) {
        // relative width
        width = window.innerWidth * width;
        if (width < 1024) {
          width = 1024;
        }
      }

      let height = data.height ?? 500;
      if ( height <= 1.1 ) {
        // relative width
        height = window.innerHeight * height;
        if (height < 400) {
          height = 400;
        }
      }
  
      if (!this.widget) {
        this.widget = new ViewerWrapper({
          $container : this.el, cache : global_cache,
          width : width, height : height,
          // do not automatically scale the brain to fit the screen
          viewerMode : false
        });
      }
      this.widget.receiveData({ data : data, reset : false });
    } catch (error) {
      console.log('error', error);
    }
    // widget.viewer.shinyDriver = new threeBrain.Drivers.Shiny( widget.viewer );
  }

  resize() {
    if (this.widget) {
      let width = this.el.clientWidth;
      let height = this.el.clientHeight;
      // Do not resize immediately, wait for the browser to finish resizing
      setTimeout(() => {
        let newWidth = this.el.clientWidth;
        let newHeight = this.el.clientHeight;
        if( newWidth == width && newHeight == height ) {
          if( width < 768 ) width = 768;
          if( height < 300 ) height = 300;
          this.widget.resize(width, height);
        }
      }, 100);
    }
  }
}
