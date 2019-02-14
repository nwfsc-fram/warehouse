/**
 * [Select2](http://ivaynberg.github.io/select2) is a replacement for HTML
 * `-tag select` elements, enhancing standard `-tag select`'s with searching,
 * remote data sets and more. This plug-in provides the ability to use Select2
 * with Editor very easily.
 *
 * @name Select2
 * @summary Use the Select2 library with Editor for complex select input options.
 * @requires [Select2](http://ivaynberg.github.io/select2)
 * @depcss //cdnjs.cloudflare.com/ajax/libs/select2/4.0.2/css/select2.min.css
 * @depjs //cdnjs.cloudflare.com/ajax/libs/select2/4.0.2/js/select2.min.js
 * 
 * @opt `e-type object` **`options`**: - The values and labels to be used in the Select2 list. This can be given in a number of different forms:
 *   * `e-type object` - Name / value pairs, where the property name is used as the label and the value as the field value. For example: `{ "Edinburgh": 51, "London": 76, ... }`.
 *   * `e-type array` - An array of objects with the properties `label` and `value` defined. For example: `[ { label: "Edinburgh", value: 51 }, { label: "London", value: 76 } ]`.
 *   * `e-type array` - An array of values (e.g. numbers, strings etc). Each element in the array will be used for both the label and the value. For example: `[ "Edinburgh", "London" ]`.
 * @opt `e-type object` **`opts`**: Select2 initialisation options object.
 *     Please refer to the Select2 documentation for the full range
 *     of options available.
 * @opt `e-type object` **`attr`**: Attributes that are applied to the
 *     `-tag select` element before Select2 is initialised
 *
 * @method **`inst`**: Execute a Select2 method, using the arguments given. The
 *     return value is that returned by the Select2 method. For example you could
 *     use `editor.field('priority').inst('val')` to get the value from Select2
 *     directly.
 * @method **`update`**: Update the list of options that are available in the
 *     Select2 list. This uses the same format as `options` for the
 *     initialisation.
 *
 * @example
 * // Create an Editor instance with a Select2 field and data
 * new $.fn.dataTable.Editor( {
 *   "ajax": "php/todo.php",
 *   "table": "#example",
 *   "fields": [ {
 *           "label": "Item:",
 *           "name": "item"
 *       }, {
 *           "label": "Priority:",
 *           "name": "priority",
 *           "type": "select2",
 *           "options": [
 *               { "label": "1 (highest)", "value": "1" },
 *               { "label": "2",           "value": "2" },
 *               { "label": "3",           "value": "3" },
 *               { "label": "4",           "value": "4" },
 *               { "label": "5 (lowest)",  "value": "5" }
 *           ]
 *       }, {
 *           "label": "Status:",
 *           "name": "status",
 *           "type": "radio",
 *           "default": "Done",
 *           "options": [
 *               { "label": "To do", "value": "To do" },
 *               { "label": "Done", "value": "Done" }
 *           ]
 *       }
 *   ]
 * } );
 *
 * @example
 * // Add a Select2 field to Editor with Select2 options set
 * editor.add( {
 *     "label": "State:",
 *     "name": "state",
 *     "type": "select2",
 *     "opts": {
 *         "placeholder": "Select State",
 *         "allowClear": true
 *     }
 * } );
 * 
 */

(function( factory ){
	if ( typeof define === 'function' && define.amd ) {
		// AMD
		define( ['jquery', 'datatables', 'datatables-editor'], factory );
	}
	else if ( typeof exports === 'object' ) {
		// Node / CommonJS
		module.exports = function ($, dt) {
			if ( ! $ ) { $ = require('jquery'); }
			factory( $, dt || $.fn.dataTable || require('datatables') );
		};
	}
	else if ( jQuery ) {
		// Browser standard
		factory( jQuery, jQuery.fn.dataTable );
	}
}(function( $, DataTable ) {
'use strict';


if ( ! DataTable.ext.editorFields ) {
	DataTable.ext.editorFields = {};
}

var _fieldTypes = DataTable.Editor ?
    DataTable.Editor.fieldTypes :
    DataTable.ext.editorFields;


_fieldTypes.select2 = {
	_addOptions: function ( conf, opts ) {
		var elOpts = conf._input[0].options;

		elOpts.length = 0;

		if ( opts ) {
			DataTable.Editor.pairs( opts, conf.optionsPair, function ( val, label, i ) {
				elOpts[i] = new Option( label, val );
			} );
		}
	},

	create: function ( conf ) {
		conf._input = $('<select/>')
			.attr( $.extend( {
				id: DataTable.Editor.safeId( conf.id )
			}, conf.attr || {} ) );

		var options = $.extend( {
				width: '100%'
			}, conf.opts );

		_fieldTypes.select2._addOptions( conf, conf.options || conf.ipOpts );
		conf._input.select2( options );

		// On open, need to have the instance update now that it is in the DOM
		this.on( 'open.select2-'+DataTable.Editor.safeId( conf.id ), function () {
			conf._input.select2( options );
		} );

		return conf._input[0];
	},

	get: function ( conf ) {
		var val = conf._input.val();

		return conf._input.prop('multiple') && val === null ?
			[] :
			val;
	},

	set: function ( conf, val ) {
		conf._input.val( val ).trigger( 'change', {editor: true} );
	},

	enable: function ( conf ) {
		$(conf._input).removeAttr( 'disabled' );
	},

	disable: function ( conf ) {
		$(conf._input).attr( 'disabled', 'disabled' );
	},

	// Non-standard Editor methods - custom to this plug-in
	inst: function ( conf ) {
		var args = Array.prototype.slice.call( arguments );
		args.shift();

		return conf._input.select2.apply( conf._input, args );
	},

	update: function ( conf, data ) {
		_fieldTypes.select2._addOptions( conf, data );
		$(conf._input).trigger('change');
	},

	focus: function ( conf ) {
		conf._input.select2('open');
	}
};


}));
