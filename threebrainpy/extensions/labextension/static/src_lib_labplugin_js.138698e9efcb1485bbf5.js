"use strict";
(self["webpackChunkthreebrainpy"] = self["webpackChunkthreebrainpy"] || []).push([["src_lib_labplugin_js"],{

/***/ "./src/lib/index.js":
/*!**************************!*\
  !*** ./src/lib/index.js ***!
  \**************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   BrainWidgetModel: () => (/* reexport safe */ _widget__WEBPACK_IMPORTED_MODULE_1__.BrainWidgetModel),
/* harmony export */   BrainWidgetView: () => (/* reexport safe */ _widget__WEBPACK_IMPORTED_MODULE_1__.BrainWidgetView),
/* harmony export */   version: () => (/* binding */ version)
/* harmony export */ });
/* harmony import */ var _package_json__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../package.json */ "./package.json");
/* harmony import */ var _widget__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./widget */ "./src/lib/widget.js");
// Export widget models and views, and the npm package version number.


const version = _package_json__WEBPACK_IMPORTED_MODULE_0__.version;


console.log(version);



/***/ }),

/***/ "./src/lib/labplugin.js":
/*!******************************!*\
  !*** ./src/lib/labplugin.js ***!
  \******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   brainWidgetPlugin: () => (/* binding */ brainWidgetPlugin),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _index__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./index */ "./src/lib/index.js");
/* harmony import */ var _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyter-widgets/base */ "webpack/sharing/consume/default/@jupyter-widgets/base");
/* harmony import */ var _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_1__);



const brainWidgetPlugin = {
  id: 'threebrainpy:plugin',
  requires: [_jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_1__.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'threebrainpy',
          version: _index__WEBPACK_IMPORTED_MODULE_0__.version,
          exports: { BrainWidgetModel: _index__WEBPACK_IMPORTED_MODULE_0__.BrainWidgetModel, BrainWidgetView: _index__WEBPACK_IMPORTED_MODULE_0__.BrainWidgetView }
      });
  },
  autoStart: true
};

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (brainWidgetPlugin);


/***/ }),

/***/ "./src/lib/widget.js":
/*!***************************!*\
  !*** ./src/lib/widget.js ***!
  \***************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   BrainWidgetModel: () => (/* binding */ BrainWidgetModel),
/* harmony export */   BrainWidgetView: () => (/* binding */ BrainWidgetView)
/* harmony export */ });
/* harmony import */ var _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyter-widgets/base */ "webpack/sharing/consume/default/@jupyter-widgets/base");
/* harmony import */ var _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _rave_ieeg_three_brain_src_js_index_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @rave-ieeg/three-brain/src/js/index.js */ "./node_modules/@rave-ieeg/three-brain/src/js/index.js");




const global_cache = window.global_cache || new _rave_ieeg_three_brain_src_js_index_js__WEBPACK_IMPORTED_MODULE_1__.StorageCache();
window.global_cache = global_cache;
window.THREE = _rave_ieeg_three_brain_src_js_index_js__WEBPACK_IMPORTED_MODULE_1__.ExternLibs.THREE;

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

class BrainWidgetModel extends _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_0__.DOMWidgetModel {
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

class BrainWidgetView extends _jupyter_widgets_base__WEBPACK_IMPORTED_MODULE_0__.DOMWidgetView {

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
        this.widget = new _rave_ieeg_three_brain_src_js_index_js__WEBPACK_IMPORTED_MODULE_1__.ViewerWrapper({
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


/***/ }),

/***/ "./package.json":
/*!**********************!*\
  !*** ./package.json ***!
  \**********************/
/***/ ((module) => {

module.exports = JSON.parse('{"name":"threebrainpy","version":"0.1.0","description":"Your Advanced Electrode Localizer Viewer for Python","main":"src/lib/index.js","files":["src/**/*.js","dist/*.js"],"scripts":{"clean":"rimraf dist/ && rimraf threebrainpy/extensions/labextension/ && rimraf threebrainpy/extensions/nbextension","test":"echo \\"Error: no test specified\\" && exit 1","watch":"webpack --watch --mode=development","docs":"mkdocs build","docs-serve":"mkdocs serve -w threebrainpy","docs-deploy":"mkdocs gh-deploy","build":"webpack --mode=development && yarn run build:labextension:dev","build:prod":"webpack --mode=production && yarn run build:labextension","build:labextension":"jupyter labextension build .","build:labextension:dev":"jupyter labextension build --development True .","rebuild":"yarn run build && jupyter labextension develop . --overwrite"},"repository":{"type":"git","url":"git+https://github.com/dipterix/threebrainpy.git"},"keywords":["iEEG","DBS","Visualization","Neuroscience","Electrophysiology","Electrode","Localizer"],"author":"Zhengjia Wang","license":"MPL-2.0","bugs":{"url":"https://github.com/dipterix/threebrainpy/issues"},"homepage":"https://github.com/dipterix/threebrainpy","devDependencies":{"@jupyterlab/builder":"^4.0.5","rimraf":"^2.7.1","webpack":"^5.88.2"},"dependencies":{"@jupyter-widgets/base":"^1.1 || ^2 || ^3 || ^4 || ^6","@jupyterlab/services":"^7.0.5","@rave-ieeg/three-brain":"^1.0.1","react":"^18.2.0"},"jupyterlab":{"extension":"src/lib/labplugin","outputDir":"threebrainpy/extensions/labextension","sharedPackages":{"@jupyter-widgets/base":{"bundled":false,"singleton":true}}}}');

/***/ })

}]);
//# sourceMappingURL=src_lib_labplugin_js.138698e9efcb1485bbf5.js.map