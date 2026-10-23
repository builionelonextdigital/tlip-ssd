/** @odoo-module **/

import { Component, useState, useEffect, useRef, onWillUnmount } from "@odoo/owl";
import { renderToString } from "@web/core/utils/render";

export class PlanRenderer extends Component {
    setup() {
        this.model = this.props.model;
        this.state = useState({
            currentLocationId: (!this.model.data.isParentLocation && this.model.metaData.resId) || null,
            locationEditMode: false,
            layoutData: this.props.model.data.layoutData || []
        });
        this.tooltipData = this.props.model.data.tooltipData || [];
        this.leafletMap = null;
        this.drawControl = null;
        this.editableLayers = null;
        this.readOnlyLayers = null;
        this.currentLocationLayers = [];
        this.deletableLocationLayers = [];
        this.planContainerRef = useRef("planContainer");
        this.locationSelectorRef = useRef("locationSelector");
        this.layoutWidth = 1635;
        this.layoutHeight = 700;
        this.mode = this.model.metaData.mode;
        L.customLabelLayer = L.Rectangle.extend({
            initialize: function (latLngBounds, label, layer, options) {
                L.Rectangle.prototype.initialize.call(this, latLngBounds, options);
                this._label = label;
                this._layer = layer;
                L.Util.setOptions(this, options);
            },

            options: {
                offset: new L.Point(0, 0)
            },

            onAdd: function (map) {
                this._container = L.Rectangle.prototype.onAdd.call(this, map);
                this.map = map;

                if (!this._container) {
                    this._container = L.DomUtil.create('div', 'leaflet-label-overlay');
                    this._container.innerHTML = this._label;
                    this._updateBounds(map);
                    map.getPanes().markerPane.appendChild(this._container);
                    this._updateEnd();

                    map.on('movestart', this._updateStart, this);
                    map.on('moveend', this._updateEnd, this);
                    this._container.addEventListener('mouseover', (e) => {
                        this._layer.openTooltip();
                    })
                    this._container.addEventListener('mouseout', (e) => {
                        this._layer.closeTooltip();
                    })
                }
                return this._container
            },

            onRemove: function (map) {
                L.Rectangle.prototype.onRemove.call(this, map);
                map.getPanes().markerPane.removeChild(this._container);
                map.off('movestart', this._updateStart, this);
                map.off('moveend', this._updateEnd, this);
            },

            _updateBounds: function (map) {
                if (!map) {
                    return;
                }
                const northEast = map.latLngToLayerPoint(this.getBounds().getNorthEast());
                const southWest = map.latLngToLayerPoint(this.getBounds().getSouthWest());
                var width = Math.abs(northEast.x - southWest.x);
                var height = Math.abs(northEast.y - southWest.y);

                var fontSize = height / 5;
                if (fontSize < 7) {
                    fontSize = 7
                }

                this._container.style.width = width + 'px';
                this._container.style.height = height + 'px';
                this._container.style.fontSize = fontSize + 'px';
            },

            _updateStart: function () {
                L.DomUtil.setPosition(this._container, 0);
                this._container.style.opacity = 0;
            },

            _updateEnd: function () {
                const pos = this.map.latLngToLayerPoint(this.getBounds().getNorthWest());
                var op = new L.Point(pos.x, pos.y);
                L.DomUtil.setPosition(this._container, op);
                this._container.style.opacity = 1;
                this._updateBounds(this.map);
            },
        })

        onWillUnmount(this.removeLeafletMap);

        useEffect(
            () => {
                this.leafletMap = L.map(this.planContainerRef.el, {
                    editable: true,
                    crs: L.CRS.Simple,
                    zoomDelta: 0.3,
                    zoomSnap: 0.3,
                    scrollWheelZoom: 'center',
                    wheelPxPerZoomLevel: 200,
                    minZoom: -5,
                    maxZoom: 5,
                    renderer: L.canvas()
                });
                this.leafletMap
                    .on(L.Draw.Event.CREATED, this._drawCreated, this)
                    .on(L.Draw.Event.DELETESTOP, this._drawDeleted, this);

                const bound = [[0, 0], [this.layoutHeight, this.layoutWidth]];
                L.imageOverlay(this.model.data.layoutImageUrl, bound).addTo(this.leafletMap);
                this.leafletMap.fitBounds(bound);
                this.editableLayers = new L.FeatureGroup();
                this.editableLayers
                    .on('layeradd', this._addLayer, this)
                    .on('layerremove', this._removeLayer, this);
                this.leafletMap.addLayer(this.editableLayers);

                this.readOnlyLayers = new L.FeatureGroup();
                this.leafletMap.addLayer(this.readOnlyLayers);
            },
            () => []
        );

        useEffect(
            () => {
                if (this.props.enableDrawControl) {
                    this.enableDrawControl();
                }
                else {
                    this.disableDrawControl();
                }

            },
            () => [this.props.enableDrawControl]
        );

        useEffect(
            () => {
                if (this.props.isSaving) {
                    const layoutDataToSave = this.exportLayoutData();
                    this.props.onSave(layoutDataToSave);
                    this.state.layoutData = layoutDataToSave;
                    if (this.locationSelectorRef.el) {
                        this.locationSelectorRef.el.value = '';
                    }
                }
            },
            () => [this.props.isSaving]
        );

        useEffect(
            () => {
                this.readOnlyLayers.eachLayer((layer) => {
                    this.readOnlyLayers.removeLayer(layer);
                    if (layer.labelLayer) {
                        this.leafletMap.removeLayer(layer.labelLayer);
                    }
                })

                this.editableLayers.eachLayer((layer) => {
                    this.editableLayers.removeLayer(layer);
                    if (layer.labelLayer) {
                        this.leafletMap.removeLayer(layer.labelLayer);
                    }
                })

                this._renderLocations(this.state.layoutData);
            },
            () => [this.state.layoutData]
        );

        useEffect(
            () => {
                if (this.props.discard) {
                    this.discard();
                }
            },
            () => [this.props.discard]
        );
    }

    onSelectLocation(event) {
        const locationId = parseInt(event.target.value);
        if (!locationId) {
            return;
        }
        if (this.state.currentLocationId && this.state.currentLocationId != locationId) {
            this.disableDrawControl();
        }
        this.state.currentLocationId = locationId;
        this.currentLocationLayers = [];

        this.editableLayers.eachLayer((layer) => {
            if (layer.locationId != locationId) {
                const layerId = this.editableLayers.getLayerId(layer);
                this.editableLayers._layers[layerId] = undefined;
                this.readOnlyLayers.addLayer(layer);
                delete this.editableLayers._layers[layerId];
            }
        });
        this.readOnlyLayers.eachLayer((layer) => {
            if (layer.locationId == locationId) {
                const layerId = this.readOnlyLayers.getLayerId(layer);
                this.readOnlyLayers._layers[layerId] = undefined;
                this.editableLayers.addLayer(layer);
                delete this.readOnlyLayers._layers[layerId];
            }
        })

        this.editableLayers.eachLayer((layer) => {
            this.currentLocationLayers.push(layer);
        });

        this.props.onEdit();
        this.enableDrawControl();

    }

    removeLeafletMap() {
        if (this.leafletMap) {
            this.leafletMap.remove();
        }
        this.currentLocationLayers = [];
    }

    _drawCreated(e) {
        const layer = e.layer;
        layer.locationId = this.state.currentLocationId;
        this.editableLayers.addLayer(layer);
        this.currentLocationLayers.push(layer);
    }

    _drawDeleted(e) {
        this.currentLocationLayers = this.currentLocationLayers.filter(layer => !this.deletableLocationLayers.includes(layer));
        this.deletableLocationLayers = [];
    }

    _addLayer(e) {
        const layer = e.layer;

        const layerIndex = this.currentLocationLayers.indexOf(layer);
        if (layerIndex != -1) {
            this.deletableLocationLayers.splice(layerIndex, 1);
        }
    }

    _removeLayer(e) {
        const layer = e.layer;
        this.deletableLocationLayers.push(layer);
    }

    discard() {
        if (this.locationSelectorRef.el) {
            this.locationSelectorRef.el.value = '';
        }

        const locationLayers = this.readOnlyLayers.getLayers()
            .concat(this.editableLayers.getLayers())

        for (const layer of locationLayers) {
            this.leafletMap.removeLayer(layer);
            if (layer.labelLayer) {
                this.leafletMap.removeLayer(layer.labelLayer);
            }
        }

        this._renderLocations(this.state.layoutData);
    }

    enableDrawControl() {
        const drawControl = this.getDrawControl();
        this.leafletMap.addControl(drawControl);

        this.currentLocationLayers.forEach((locationLayer) => {
            locationLayer.editing.enable();
            locationLayer.unbindTooltip();
            if (locationLayer.labelLayer) {
                this.leafletMap.removeLayer(locationLayer.labelLayer);
                locationLayer.labelLayer = null;
            }
        })
    }

    disableDrawControl() {
        if (this.drawControl) {
            this.leafletMap.removeControl(this.drawControl);
        }

        this.currentLocationLayers.forEach((locationLayer) => {
            locationLayer.editing.disable();
        })

        if (this.state.currentLocationId) {
            const locationTooltipData = this.tooltipData.find(d => d.location_id === this.state.currentLocationId)
            const xml = renderToString("web_plan_layout.Tooltip", {
                data: locationTooltipData
            });
            this.currentLocationLayers.forEach((locationLayer) => {
                locationLayer.bindTooltip(xml, {
                    permanent: false
                });
                if (!locationLayer.labelLayer) {
                    this._renderLabel(locationLayer, locationTooltipData);
                }
            })
        }
    }

    getDrawControl() {
        if (!this.drawControl) {
            this.drawControl = new L.Control.Draw(this.getDrawControlOptions(this.editableLayers, this.mode));
        }
        return this.drawControl
    }

    getDrawControlOptions(editableLayers, mode) {
        return {
            position: 'topleft',
            draw: {
                polyline: false,
                marker: false,
                circlemarker: false,
                polygon: mode === 'editable' ? {
                    allowIntersection: false, // Restricts shapes to simple polygons
                    drawError: {
                        color: '#e1e100', // Color the shape will turn when intersects
                        message: '<strong>Oh snap!<strong> you can\'t draw that!' // Message that will show when intersect
                    },
                    shapeOptions: {
                        color: '#bada55'
                    }
                } : false,
                rectangle: mode === 'editable' ? {
                    shapeOptions: {
                        clickable: true,
                        color: '#bada55'
                    }
                } : false,
                circle: mode === 'editable' ? {
                    shapeOptions: {
                        clickable: true,
                        color: '#bada55'
                    }
                } : false
            },
            edit: mode === 'editable' ? {
                featureGroup: editableLayers,
                remove: true
            } : false
        }
    }

    _renderLabel(layer, locationTooltipData) {
        const northWestPoint = layer.getBounds().getNorthWest();
        const southEastPoint = layer.getBounds().getSouthEast();
        const height = Math.abs(northWestPoint.lat - southEastPoint.lat);

        const corner1 = L.latLng(northWestPoint.lat - height / 4, northWestPoint.lng)
        const corner2 = L.latLng(southEastPoint.lat + height / 4, southEastPoint.lng)
        const labelBounds = L.latLngBounds(corner1, corner2);

        const labelLayer = new L.customLabelLayer(
            labelBounds,
            renderToString("web_plan_layout.Label", {
                data: locationTooltipData
            }),
            layer
        );
        layer.labelLayer = labelLayer;
        labelLayer.setStyle({
            fillOpacity: 0,
            stroke: false
        });

        this.leafletMap.addLayer(labelLayer);
        return labelLayer
    }

    _renderLocations(layoutData) {
        var self = this;
        layoutData.forEach((layer) => {
            var locationLayer = null;
            const locationTooltipData = self.tooltipData.find(d => d.location_id === layer.location_id);
            if (locationTooltipData == undefined) {
                return;
            }
            if (layer.type === 'Rectangle') {
                locationLayer = L.rectangle(layer.data.bounds);
            } else if (layer.type === 'Circle') {
                locationLayer = L.circle(layer.data.center, { radius: layer.data.radius });
            }
            else {
                const coordinates = layer.data.map((coordinate) => {
                    return [coordinate[1], coordinate[0]]
                });
                locationLayer = L.polygon(coordinates);
            }

            if (locationLayer) {
                locationLayer.setStyle({
                    weight: 1,
                    fillOpacity: 0.6,
                    fillColor: locationTooltipData.color,
                });
                locationLayer.locationId = layer.location_id;

                if (self.model.metaData.resModel === 'stock.location' && self.model.metaData.resId == layer.location_id) {
                    self.currentLocationLayers.push(locationLayer);
                }

                if (layer.location_id === self.state.currentLocationId) {
                    self.editableLayers.addLayer(locationLayer);
                }
                else {
                    self.readOnlyLayers.addLayer(locationLayer);
                }
                self._renderLabel(locationLayer, locationTooltipData);

                const xml = renderToString("web_plan_layout.Tooltip", {
                    data: locationTooltipData
                });
                locationLayer.bindTooltip(xml, {
                    permanent: false
                });
            }
        })
    }

    exportLayoutData() {
        var self = this;
        var layoutDataToExport = this.state.layoutData.filter(d => d.location_id != self.state.currentLocationId);

        this.currentLocationLayers.forEach((locationLayer) => {
            if (locationLayer instanceof L.Circle) {
                var center = locationLayer.getLatLng();
                var coordinates = {
                    center: [center.lat, center.lng],
                    radius: locationLayer.getRadius()
                };
            } else if (locationLayer instanceof L.Rectangle) {
                const bounds = locationLayer.getBounds();
                const boundNorthWest = bounds.getNorthWest();
                const boundSouthEast = bounds.getSouthEast();
                var coordinates = {
                    bounds: [
                        [boundNorthWest.lat, boundNorthWest.lng],
                        [boundSouthEast.lat, boundSouthEast.lng]
                    ]
                };
            } else {
                const geoJSON = locationLayer.toGeoJSON();
                var coordinates = geoJSON.geometry.coordinates[0];
            }

            if (locationLayer instanceof L.Circle) {
                var type = 'Circle';
            } else if (locationLayer instanceof L.Rectangle) {
                var type = 'Rectangle';
            } else {
                var type = 'Polygon';
            }

            layoutDataToExport.push({
                location_id: this.state.currentLocationId,
                type: type,
                data: coordinates
            })
        });

        return layoutDataToExport
    }
}

PlanRenderer.template = "web_plan_layout.PlanRenderer";
PlanRenderer.props = {
    model: Object,
    resModel: { type: String },
    locationList: { type: Array },
    isParentLocation: { type: Boolean},
    enableDrawControl: { type: Boolean },
    discard: { type: Boolean },
    isSaving: { type: Boolean },
    onEdit: Function,
    onSave: Function
};

