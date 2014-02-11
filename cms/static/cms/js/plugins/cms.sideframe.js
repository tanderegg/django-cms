/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Sideframe
	 * Controls a cms specific sideframe
	 */
	CMS.Sideframe = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'sideframeDuration': 300,
			'sideframeWidth': 320,
			'urls': {
				'css_sideframe': 'cms/css/plugins/cms.toolbar.sideframe.css'
			}
		},

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);
			this.config = CMS.config;
			this.settings = CMS.settings;

			// elements
			this.sideframe = $('.cms_sideframe');
			this.body = $('html');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms';
			this.enforceReload = false;

			// if the modal is initialized the first time, set the events
			if(!this.sideframe.data('ready')) this._events();

			// ready sideframe
			this.sideframe.data('ready', true);
		},

		// initial methods
		_events: function () {
			var that = this;

			// attach close event
			this.sideframe.find('.cms_sideframe-close').bind(this.click, function () {
				that.close(true);
			});

			// attach hide event
			this.sideframe.find('.cms_sideframe-hide').bind(this.click, function () {
				if($(this).hasClass('cms_sideframe-hidden')) {
					that.settings.sideframe.hidden = false;
					that._show(that.settings.sideframe.position || that.options.sideframeWidth, true);
				} else {
					that.settings.sideframe.hidden = true;
					that._hide();
				}
				that.settings = that.setSettings(that.settings);
			});

			// attach maximize event
			this.sideframe.find('.cms_sideframe-maximize').bind(this.click, function () {
				if($(this).hasClass('cms_sideframe-minimize')) {
					that.settings.sideframe.maximized = false;
					that._minimize();
				} else {
					that.settings.sideframe.maximized = true;
					that.settings.sideframe.hidden = false;
					that._maximize();
				}
				that.settings = that.setSettings(that.settings);
			});

			this.sideframe.find('.cms_sideframe-resize').bind('mousedown', function (e) {
				e.preventDefault();
				that._startResize();
			});

			// stopper events
			$(document).bind('mouseup.cms', function () {
				that._stopResize();
			});
		},

		// public methods
		open: function (url, animate) {
			// prepare iframe
			var that = this;
			var holder = this.sideframe.find('.cms_sideframe-frame');
			var iframe = $('<iframe src="'+url+'" class="" frameborder="0" />');
				iframe.hide();
			var width = this.settings.sideframe.position || this.options.sideframeWidth;

			// attach load event to iframe
			iframe.bind('load', function () {
				// after iframe is loaded append css
				iframe.contents().find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.config.urls.static + that.options.urls.css_sideframe + '" />'));
				// remove loader
				that.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');
				// than show
				iframe.show();
				// if a message is triggerd, refresh
				var messages = iframe.contents().find('.messagelist li');
				if(messages.length || that.enforceReload) {
					that.enforceReload = true;
				} else {
					that.enforceReload = false;
				}

				// add debug infos
				if(that.config.debug) iframe.contents().find('body').addClass('cms_debug');

				// save url in settings
				that.settings.sideframe.url = iframe.get(0).contentWindow.location.href;
				that.settings = that.setSettings(that.settings);

				// bind extra events
				iframe.contents().find('body').bind(that.click, function () {
					$(document).trigger(that.click);
				});
			});

			// cancel animation if sideframe is already shown
			if(this.sideframe.is(':visible')) {
				// sideframe is already open
				insertHolder(iframe);
				// reanimate the frame
				if(parseInt(this.sideframe.css('width')) <= width) this._show(width, animate);
			} else {
				// load iframe after frame animation is done
				setTimeout(function () {
					insertHolder(iframe);
				}, this.options.sideframeDuration);
				// display the frame
				this._show(width, animate);
			}

			function insertHolder(iframe) {
				// show iframe after animation
				that.sideframe.find('.cms_sideframe-frame').addClass('cms_loader');
				holder.html(iframe);
			}
		},

		close: function () {
			this._hide(true);

			// remove url in settings
			this.settings.sideframe = {
				'url': null,
				'hidden': false,
				'maximized': false,
				'width': this.options.sideframeWidth
			};

			this.settings = this.setSettings(this.settings);
		},

		// private methods
		_show: function (width, animate) {
			// add class
			this.sideframe.find('.cms_sideframe-hide').removeClass('cms_sideframe-hidden');
			
			// make sure the close / hide / maximize controls appear, regardless of hidden / maximized state
			this.sideframe.show();

			// check if sideframe should be hidden
			if(this.settings.sideframe.hidden) this._hide();

			// check if sideframe should be maximized
			if(this.settings.sideframe.maximized) this._maximize();

			// otherwise do normal behaviour
			if(!this.settings.sideframe.hidden && !this.settings.sideframe.maximized) {
				if(animate) {
					this.sideframe.animate({ 'width': width }, this.options.sideframeDuration);
					this.body.animate({ 'margin-left': width }, this.options.sideframeDuration);
				} else {
					this.sideframe.animate({ 'width': width }, 0);
					this.body.animate({ 'margin-left': width }, 0);
				}
				this.sideframe.find('.cms_sideframe-btn').css('right', -20);
			}

			// lock toolbar, set timeout to make sure CMS.API is ready
			setTimeout(function () {
				CMS.API.Toolbar._lock(true);
			}, 100);
		},

		_hide: function (close) {
			// add class
			this.sideframe.find('.cms_sideframe-hide').addClass('cms_sideframe-hidden');

			var duration = this.options.sideframeDuration;
			// remove the iframe
			if(close && this.sideframe.width() <= 0) duration = 0;
			if(close) this.sideframe.find('iframe').remove();
			this.sideframe.animate({ 'width': 0 }, duration, function () {
				if(close) $(this).hide();
			});
			this.body.animate({ 'margin-left': 0 }, duration);
			this.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');

			// should we reload
			if(this.enforceReload) this.reloadBrowser();

			// lock toolbar, set timeout to make sure CMS.API is ready
			setTimeout(function () {
				CMS.API.Toolbar._lock(false);
			}, 100);
		},

		_minimize: function () {
			this.sideframe.find('.cms_sideframe-maximize').removeClass('cms_sideframe-minimize');
			this.sideframe.find('.cms_sideframe-hide').show();

			// hide scrollbar
			this.preventScroll(false);

			// reset to first state
			this._show(this.settings.sideframe.position || this.options.sideframeWidth, true);

			// remove event
			$(window).unbind('resize.cms');
		},

		_maximize: function () {
			var that = this;

			this.sideframe.find('.cms_sideframe-maximize').addClass('cms_sideframe-minimize');
			this.sideframe.find('.cms_sideframe-hide').hide();

			// reset scrollbar
			this.preventScroll(true);

			this.sideframe.find('.cms_sideframe-hide').removeClass('cms_sideframe-hidden').hide();
			// do custom animation
			this.sideframe.animate({ 'width': $(window).width() }, 0);
			this.body.animate({ 'margin-left': 0 }, 0);
			// invert icon position
			this.sideframe.find('.cms_sideframe-btn').css('right', -2);
			// attach resize event
			$(window).bind('resize.cms', function () {
				that.sideframe.css('width', $(window).width());
			});
		},

		_startResize: function () {
			var that = this;
			var timer = function () {};
			// this prevents the iframe from being focusable
			this.sideframe.find('.cms_sideframe-shim').css('z-index', 20);

			$(document).bind('mousemove.cms', function (e) {
				if(e.clientX <= 320) e.clientX = 320;

				that.sideframe.css('width', e.clientX);
				that.body.css('margin-left', e.clientX);

				// update settings
				that.settings.sideframe.position = e.clientX;

				// save position
				clearTimeout(timer);
				timer = setTimeout(function () {
					that.settings = that.setSettings(that.settings);
				}, 500);
			});
		},

		_stopResize: function () {
			this.sideframe.find('.cms_sideframe-shim').css('z-index', 1);

			$(document).unbind('mousemove.cms');
		}

	});

});
})(CMS.$);
