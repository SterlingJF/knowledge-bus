"use strict";
(() => {
  // styles/patterns.css
  var patterns_default = ".shell {\n  position: relative;\n  width: 100%;\n  height: 100%;\n  display: flex;\n  flex-direction: column;\n  overflow: hidden;\n  background: var(--kb-canvas);\n  color: var(--kb-text);\n  font: var(--kb-type-body) / var(--kb-leading-normal) var(--kb-font-sans);\n  color-scheme: light dark;\n  container-type: inline-size;\n}\n.shell[data-theme='light'] {\n  color-scheme: light;\n}\n.shell[data-theme='dark'] {\n  color-scheme: dark;\n}\n.shell *,\n.shell *::before,\n.shell *::after {\n  box-sizing: border-box;\n}\n.shell [hidden] {\n  display: none !important;\n}\n.shell :where(button) {\n  font: inherit;\n  color: var(--kb-text);\n  background: transparent;\n  border: var(--kb-stroke-xs) solid transparent;\n  border-radius: var(--kb-radius-md);\n  padding: var(--kb-space-2) var(--kb-space-2-5);\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  gap: var(--kb-space-2);\n  cursor: pointer;\n  white-space: nowrap;\n  transition: var(--kb-control-transition);\n}\n.shell :where(button):disabled {\n  opacity: var(--kb-opacity-disabled);\n  cursor: default;\n}\n.shell :where(button):focus-visible,\n.shell :where(input):focus-visible,\n.shell summary:focus-visible,\n.shell [tabindex]:focus-visible {\n  outline: var(--kb-stroke-md) solid var(--kb-focus);\n  outline-offset: var(--kb-space-0-75);\n}\n.shell h1,\n.shell h2,\n.shell h3,\n.shell p {\n  margin: 0;\n}\n.icon {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n  flex: none;\n  overflow: visible;\n  stroke-width: var(--kb-stroke-sm);\n}\n\n.topbar {\n  position: relative;\n  display: grid;\n  grid-template-columns: minmax(var(--kb-size-2xl), 1fr) auto minmax(var(--kb-topbar-utilities-column), 1fr);\n  align-items: center;\n  gap: var(--kb-space-4);\n  padding: var(--kb-space-3) var(--kb-space-4);\n  min-height: var(--kb-size-lg);\n  background: var(--kb-canvas);\n  z-index: var(--kb-layer-over-viewport);\n  flex: none;\n}\n.identity {\n  min-width: 0;\n}\n.identity-title {\n  padding: var(--kb-space-2) var(--kb-space-1);\n  max-width: 100%;\n  gap: var(--kb-space-2);\n  border: 0;\n}\n.identity-title strong {\n  font-size: var(--kb-identity-title-text);\n  font-weight: var(--kb-weight-medium);\n  overflow: hidden;\n  text-overflow: ellipsis;\n}\n.identity-title .icon {\n  color: var(--kb-text-muted);\n}\n.stats {\n  display: flex;\n  flex-wrap: wrap;\n  gap: var(--kb-space-0-75) var(--kb-space-3);\n  padding-left: var(--kb-space-1);\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-caption);\n  line-height: var(--kb-leading-normal);\n}\n.stats b {\n  font-weight: var(--kb-weight-medium);\n  color: var(--kb-text);\n}\n.view-tabs {\n  justify-self: center;\n  display: flex;\n  background: var(--kb-surface);\n  border-radius: var(--kb-radius-lg);\n  padding: var(--kb-space-0-75);\n  gap: var(--kb-space-0-25);\n  box-shadow: var(--kb-view-tabs-box-shadow);\n}\n.view-tabs button {\n  font-size: var(--kb-type-button);\n  padding: var(--kb-space-1) var(--kb-space-2);\n  min-height: var(--kb-control-height);\n  border: 0;\n  border-radius: var(--kb-radius-md);\n}\n.utilities {\n  position: absolute;\n  top: var(--kb-space-4);\n  right: var(--kb-space-4);\n  display: flex;\n  align-items: center;\n  gap: var(--kb-space-1);\n}\n.utilities > button,\n.utilities .menu-trigger {\n  width: var(--kb-utility-control-size);\n  height: var(--kb-utility-control-size);\n  min-height: var(--kb-utility-control-size);\n  padding: var(--kb-space-1-5);\n  background: var(--kb-surface);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n  position: relative;\n}\n.active-dot {\n  position: absolute;\n  right: var(--kb-space-1-5);\n  top: var(--kb-space-1-5);\n  width: var(--kb-active-dot-size);\n  height: var(--kb-active-dot-size);\n  border-radius: var(--kb-radius-md);\n  background: var(--kb-accent);\n}\n\n.viewport {\n  position: relative;\n  flex: 1;\n  min-height: 0;\n  overflow: hidden;\n  background: var(--kb-viewport-background);\n  touch-action: none;\n  cursor: grab;\n}\n.viewport:active {\n  cursor: grabbing;\n}\n.world {\n  position: absolute;\n  left: 0;\n  top: 0;\n  transform-origin: 0 0;\n  will-change: transform;\n}\n.wires,\n.labels-layer {\n  position: absolute;\n  left: 0;\n  top: 0;\n  overflow: visible;\n  pointer-events: none;\n}\n.wires g,\n.labels-layer g {\n  pointer-events: auto;\n}\n.wire,\n.arrowhead,\n.leader {\n  pointer-events: none;\n}\n[data-connection],\n[data-label],\n[data-nub] {\n  transition: opacity var(--kb-motion-hush);\n}\n.wire {\n  fill: none;\n  stroke-width: var(--kb-connection-stroke-base);\n  transition: stroke-width var(--kb-motion-hush);\n}\n.wire[data-paint='element'] {\n  stroke: var(--kb-element);\n}\n.wire[data-paint='rolled'] {\n  stroke: var(--kb-connection-rolled);\n}\n.wire[data-paint='frame'] {\n  stroke: var(--kb-frame);\n  stroke-dasharray: var(--kb-connection-dash-frame);\n}\n.wire[data-dash='situational'] {\n  stroke-dasharray: var(--kb-connection-dash-situational);\n}\n.wire[data-dash='mixed'] {\n  stroke-dasharray: var(--kb-connection-dash-mixed);\n}\n.arrowhead[data-paint='element'] {\n  fill: var(--kb-element);\n}\n.arrowhead[data-paint='rolled'] {\n  fill: var(--kb-connection-rolled);\n}\n.arrowhead[data-paint='frame'] {\n  fill: var(--kb-frame);\n}\n.arrowhead[data-holding='links'] {\n  fill: var(--kb-surface);\n  stroke: var(--kb-element);\n  stroke-width: var(--kb-stroke-sm);\n}\n.wire-hit {\n  stroke: transparent;\n  fill: none;\n  stroke-width: var(--kb-connection-stroke-hit);\n  cursor: pointer;\n}\n.boundary {\n  position: absolute;\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-4xl);\n  pointer-events: none;\n}\n.boundary[data-role='scope'] {\n  border-color: var(--kb-boundary-scope-border);\n}\n.boundary[data-role='scope']::before,\n.boundary[data-role='group']::before {\n  content: '';\n  position: absolute;\n  inset: 0;\n  border-radius: inherit;\n  background: var(--kb-ground-frame);\n  z-index: var(--kb-layer-under-map);\n}\n.boundary-title {\n  position: absolute;\n  top: 0;\n  left: var(--kb-space-5);\n  padding: 0 var(--kb-space-3);\n  background: var(--kb-canvas);\n  color: var(--kb-text);\n  font-size: var(--kb-boundary-title-text);\n  font-weight: var(--kb-weight-medium);\n  border: 0;\n  pointer-events: auto;\n  white-space: nowrap;\n  transform: translateY(-50%) scale(var(--boundary-scale, 1));\n  transform-origin: left center;\n}\n.boundary[data-role='scope'] .boundary-title {\n  color: var(--kb-frame);\n  font-size: var(--kb-type-title);\n  gap: var(--kb-space-2);\n  border-radius: var(--kb-radius-md);\n}\n.boundary-caption {\n  position: absolute;\n  left: var(--kb-space-5);\n  top: var(--kb-boundary-caption-top);\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-normal);\n  transform: scale(var(--boundary-scale, 1));\n  transform-origin: left top;\n}\n.boundary-note {\n  position: absolute;\n  margin: 0;\n  display: grid;\n  place-items: center;\n  text-align: center;\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-normal);\n}\n\n.card {\n  position: absolute;\n  display: flex;\n  flex-direction: column;\n  align-items: stretch;\n  justify-content: flex-start;\n  gap: var(--kb-space-0-75);\n  padding: var(--kb-space-3);\n  text-align: left;\n  background: var(--kb-surface);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n  font-size: var(--kb-card-text);\n  overflow: hidden;\n  white-space: normal;\n  transition:\n    background-color var(--kb-motion-glance),\n    border-color var(--kb-motion-glance),\n    box-shadow var(--kb-motion-glance),\n    filter var(--kb-motion-glance);\n  --card-accent: var(--kb-frame);\n}\n.card > * {\n  transition: opacity var(--kb-motion-hush);\n}\n.card[data-kind='artifact'] {\n  --card-accent: var(--kb-artifact);\n  border-top: var(--kb-stroke-lg) solid var(--card-accent);\n  border-color: var(--kb-card-border-artifact);\n  background: var(--kb-card-background-artifact);\n}\n.card[data-kind='element'] {\n  --card-accent: var(--kb-element);\n  border-left: var(--kb-stroke-lg) solid var(--card-accent);\n  padding: var(--kb-space-2-5) var(--kb-space-3) var(--kb-space-3) var(--kb-card-element-indent);\n  font-size: var(--kb-type-body-lg);\n}\n.card[data-kind='frame'],\n.card[data-kind='factor'] {\n  border-top: var(--kb-stroke-lg) solid var(--card-accent);\n}\n.card:hover {\n  border-color: var(--card-accent);\n  filter: var(--kb-card-hover-filter);\n}\n.card[data-state='selected'] {\n  border-color: var(--card-accent);\n  outline: var(--kb-stroke-md) solid var(--card-accent);\n  outline-offset: var(--kb-space-0-5);\n  background: var(--kb-card-selected-background-frame);\n  box-shadow: var(--kb-card-selected-ring-frame);\n  filter: none;\n}\n.card[data-kind='element'][data-state='selected'] {\n  background: var(--kb-card-selected-background-element);\n  box-shadow: var(--kb-card-selected-ring-element);\n}\n.card[data-kind='artifact'][data-state='selected'] {\n  background: var(--kb-card-selected-background-artifact);\n  box-shadow: var(--kb-card-selected-ring-artifact);\n}\n.card[data-state='selected'] .card-title {\n  font-weight: var(--kb-weight-emphasis);\n}\n.card[data-state='dimmed'] {\n  background: var(--kb-canvas);\n  border-color: var(--kb-card-dimmed-border);\n  box-shadow: none;\n  filter: none;\n}\n.card[data-state='dimmed'][data-owner-role='scope'],\n.card[data-state='dimmed'][data-owner-role='group'] {\n  background: var(--kb-ground-frame);\n}\n.card[data-state='dimmed'] > * {\n  opacity: var(--kb-opacity-dimmed);\n}\n.card[data-state='hushed'] > * {\n  opacity: var(--kb-opacity-hushed);\n}\n.card[data-preview='true'] {\n  border-color: var(--card-accent);\n  box-shadow: var(--kb-card-preview-glow-frame);\n}\n.card[data-kind='element'][data-preview='true'] {\n  box-shadow: var(--kb-card-preview-glow-element);\n}\n.card[data-kind='artifact'][data-preview='true'] {\n  box-shadow: var(--kb-card-preview-glow-artifact);\n}\n.card[data-state='dimmed'][data-preview='true'] {\n  box-shadow: none;\n}\n.card-title {\n  display: flex;\n  align-items: flex-start;\n  gap: var(--kb-space-2);\n  font-weight: var(--kb-weight-medium);\n}\n.card-title .icon {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n}\n.card-subtitle {\n  display: block;\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body-sm);\n  line-height: var(--kb-leading-normal);\n}\n.card[data-kind='frame'] .card-subtitle,\n.card[data-kind='factor'] .card-subtitle,\n.card[data-kind='option'] .card-subtitle {\n  display: -webkit-box;\n  -webkit-box-orient: vertical;\n  overflow: hidden;\n  -webkit-line-clamp: var(--kb-card-heading-description-lines);\n}\n.card[data-kind='option'] .card-subtitle {\n  -webkit-line-clamp: var(--kb-card-heading-option-description-lines);\n}\n.world[data-heading-grown='true'] .card-title,\n.world[data-heading-grown='true'] .card-subtitle {\n  width: calc(100% / var(--card-heading-scale, 1));\n  transform: scale(var(--card-heading-scale, 1));\n  transform-origin: left top;\n}\n.card-order-icon {\n  position: absolute;\n  left: var(--kb-space-3);\n  top: var(--kb-space-3);\n  color: var(--kb-element);\n  display: flex;\n}\n.card-order-icon .icon,\n.card-frames .icon {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n}\n.card-frames {\n  position: absolute;\n  left: var(--kb-space-3);\n  bottom: var(--kb-space-2);\n  display: flex;\n  align-items: center;\n  gap: var(--kb-space-2);\n  color: var(--kb-frame);\n  height: var(--kb-card-frames-height);\n}\n.card-frames > span {\n  display: inline-flex;\n  align-items: center;\n}\n.card-frames-overflow {\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-xl);\n  padding: 0 var(--kb-space-1);\n  font-size: var(--kb-type-caption);\n  line-height: var(--kb-card-frames-overflow-height);\n}\n.card-match {\n  margin-top: auto;\n  padding-top: var(--kb-space-2);\n  border-top: var(--kb-stroke-xs) solid var(--kb-border);\n  color: var(--kb-text);\n  font-weight: var(--kb-weight-medium);\n  font-size: var(--kb-type-body-lg);\n}\n.card[data-kind='rule'] {\n  padding: var(--kb-space-5) var(--kb-card-rule-padding-x);\n  border-radius: var(--kb-radius-2xl);\n  gap: 0;\n}\n.card[data-kind='rule'] .card-title {\n  font-size: var(--kb-card-rule-title-text);\n  line-height: var(--kb-leading-tight);\n  font-weight: var(--kb-weight-medium);\n}\n.card[data-kind='rule'] .card-subtitle {\n  margin-top: var(--kb-space-2);\n}\n.card[data-kind='option'] {\n  gap: var(--kb-space-2);\n  border-radius: var(--kb-radius-md);\n  border-top: 0;\n}\n.card[data-kind='option'] .icon {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n  color: var(--kb-frame);\n}\n.card[data-kind='option'] .card-title {\n  font-size: var(--kb-type-body-lg);\n}\n.card[data-kind='option'][data-state='selected'] {\n  border-color: var(--kb-frame);\n  background: var(--kb-card-selected-background-option);\n}\n.card-stats {\n  margin-top: auto;\n  padding-top: var(--kb-space-1-5);\n  font-size: var(--kb-type-caption);\n  color: var(--kb-text-muted);\n}\n\n.count {\n  padding: 0;\n  width: var(--kb-count-size);\n  height: var(--kb-count-size);\n  transform: scale(var(--zoom-scale, 1));\n  transform-origin: top left;\n  background: var(--kb-count-surface);\n  border: var(--kb-count-border) solid var(--kb-count-edge);\n  border-radius: var(--kb-count-radius);\n  font-size: var(--kb-count-text);\n  color: var(--kb-count-ink);\n  white-space: nowrap;\n  min-height: 0;\n}\n.count-inset {\n  position: absolute;\n  right: var(--kb-count-inset);\n  bottom: var(--kb-count-inset);\n  transform-origin: bottom right;\n  z-index: var(--kb-count-layer);\n}\n.label {\n  padding: 0;\n  width: 100%;\n  height: 100%;\n  background: var(--kb-label-surface);\n  border: var(--kb-label-border) solid var(--kb-label-edge);\n  border-radius: calc(var(--kb-label-radius) * var(--zoom-scale, 1));\n  font-size: calc(var(--kb-label-text) * var(--zoom-scale, 1));\n  color: var(--kb-label-ink);\n  white-space: nowrap;\n  min-height: 0;\n}\n.leader {\n  fill: none;\n  stroke: var(--kb-label-line);\n  stroke-width: calc(var(--kb-label-leader) * var(--zoom-scale, 1));\n}\n.nub-line {\n  fill: none;\n  stroke: var(--kb-count-line);\n  stroke-width: calc(var(--kb-count-stroke) * var(--zoom-scale, 1));\n}\n\n.dock {\n  position: absolute;\n  bottom: var(--kb-space-4);\n  left: 50%;\n  transform: translateX(-50%);\n  display: flex;\n  align-items: center;\n  padding: var(--kb-space-0-75);\n  background: var(--kb-surface);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-xl);\n  box-shadow: var(--kb-dock-box-shadow-2);\n  z-index: var(--kb-layer-over-viewport);\n  max-width: calc(100% - var(--kb-size-xs));\n}\n.dock-group {\n  display: flex;\n  align-items: center;\n  gap: var(--kb-space-0-25);\n  padding: 0 var(--kb-space-0-75);\n}\n.dock-group + .dock-group {\n  border-left: var(--kb-stroke-xs) solid var(--kb-border);\n}\n.dock button {\n  min-height: var(--kb-control-height);\n  padding: var(--kb-space-1) var(--kb-space-2);\n  gap: var(--kb-space-1);\n  border-radius: var(--kb-radius-md);\n  font-size: var(--kb-type-button);\n}\n.zoom-readout {\n  min-width: var(--kb-zoom-readout-width);\n  text-align: center;\n  font-size: var(--kb-type-button);\n  color: var(--kb-text-muted);\n}\n.legend {\n  position: absolute;\n  left: var(--kb-space-4);\n  bottom: var(--kb-legend-bottom);\n  display: flex;\n  gap: var(--kb-space-4);\n  padding: var(--kb-space-1) var(--kb-space-2);\n  max-width: calc(100% - var(--kb-overlay-clearance) * 2);\n  background: var(--kb-surface);\n  border-radius: var(--kb-radius-lg);\n  box-shadow: var(--kb-lift-chrome);\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-caption);\n  pointer-events: none;\n  z-index: var(--kb-layer-over-map);\n}\n.legend .legend-swatch {\n  width: var(--kb-legend-swatch-width);\n  height: var(--kb-icon-base);\n  flex: none;\n  vertical-align: middle;\n  margin-right: var(--kb-space-1-5);\n  overflow: visible;\n}\n.legend .legend-swatch path {\n  fill: none;\n  stroke: currentColor;\n  stroke-width: var(--kb-stroke-md);\n}\n.legend span[data-key='direct'] .legend-swatch path {\n  stroke: var(--kb-element);\n}\n.legend span[data-key='rolled'] .legend-swatch path {\n  stroke: var(--kb-connection-rolled);\n}\n.legend span[data-key='situational'] .legend-swatch path {\n  stroke-dasharray: var(--kb-connection-dash-situational);\n}\n.legend span[data-key='mixed'] .legend-swatch path {\n  stroke-dasharray: var(--kb-connection-dash-mixed);\n}\n.holding-glyph {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n  flex: none;\n  vertical-align: middle;\n  margin-right: var(--kb-space-1-5);\n  overflow: visible;\n}\n.holding-glyph polygon[data-holding='owns'] {\n  fill: var(--kb-element);\n}\n.holding-glyph polygon[data-holding='links'] {\n  fill: var(--kb-surface);\n  stroke: var(--kb-element);\n  stroke-width: var(--kb-stroke-md);\n}\n.group {\n  background: none;\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n  padding: 0 var(--kb-space-3) var(--kb-space-2);\n}\n.group + .group {\n  margin-top: var(--kb-space-5);\n}\n.group .entry:last-child {\n  border-bottom: 0;\n}\n.group h4 {\n  margin: var(--kb-space-4) 0 var(--kb-space-3);\n  font-size: var(--kb-type-body);\n  font-weight: var(--kb-weight-medium);\n  color: var(--kb-text-muted);\n}\n\n.panel {\n  position: absolute;\n  background: var(--kb-surface);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-3xl);\n  box-shadow: var(--kb-panel-box-shadow);\n  display: flex;\n  flex-direction: column;\n  overflow: hidden;\n  z-index: var(--kb-layer-over-chrome);\n  max-height: min(var(--kb-panel-height-max), calc(100% * var(--kb-panel-height-fraction)));\n}\n.panel-head {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: var(--kb-space-2);\n  padding: var(--kb-space-2-5) var(--kb-space-3) var(--kb-space-2);\n  flex: none;\n}\n.panel-head strong {\n  font-size: var(--kb-panel-head-text);\n  line-height: var(--kb-leading-tight);\n  font-weight: var(--kb-weight-medium);\n}\n.close {\n  width: var(--kb-control-height);\n  height: var(--kb-control-height);\n  min-width: var(--kb-control-height);\n  padding: var(--kb-space-1-5);\n  border: 0;\n  border-radius: var(--kb-radius-md);\n  color: var(--kb-text-muted);\n  flex: none;\n}\n.close:hover,\n.close:focus-visible {\n  background: var(--kb-canvas);\n  color: var(--kb-text);\n}\n.panel-body {\n  overflow: auto;\n  overscroll-behavior: contain;\n  min-height: 0;\n  padding: var(--kb-space-4) var(--kb-space-4);\n}\n.detail {\n  left: var(--kb-overlay-clearance);\n  width: var(--kb-detail-width);\n  max-width: calc(100% - var(--kb-overlay-clearance) * 2);\n}\n.sections {\n  display: flex;\n  gap: var(--kb-space-0-5);\n  padding: 0 var(--kb-space-2) var(--kb-space-1-5);\n  border-bottom: var(--kb-stroke-xs) solid var(--kb-border);\n  flex: none;\n}\n.sections button {\n  padding: var(--kb-space-1) var(--kb-space-2);\n  min-height: var(--kb-control-height);\n  border: 0;\n  border-radius: var(--kb-radius-md);\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-button);\n}\n.detail-kind {\n  font-size: var(--kb-type-caption);\n  color: var(--kb-text-muted);\n  margin-bottom: var(--kb-space-1-5);\n}\n.detail-question {\n  font-size: var(--kb-type-title);\n  line-height: var(--kb-leading-normal);\n  margin: 0 0 var(--kb-space-4);\n}\n.section {\n  margin: var(--kb-space-5) 0 0;\n}\n.section:first-child {\n  margin-top: 0;\n}\n.section h3 {\n  font-size: var(--kb-type-body-sm);\n  font-weight: var(--kb-weight-medium);\n  color: var(--kb-text-muted);\n  margin: 0 0 var(--kb-space-3);\n}\n.section p {\n  font-size: var(--kb-type-body-lg);\n  line-height: var(--kb-leading-normal);\n}\n.facts {\n  display: grid;\n  gap: var(--kb-space-3);\n  margin: var(--kb-space-4) 0;\n}\n.facts > div {\n  display: grid;\n  grid-template-columns: var(--kb-facts-term-column) 1fr;\n  gap: var(--kb-space-3);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-normal);\n}\n.facts dt {\n  color: var(--kb-text-muted);\n}\n.facts dd {\n  margin: 0;\n}\n.entry {\n  padding: var(--kb-space-2-5) 0;\n  border-bottom: var(--kb-stroke-xs) solid var(--kb-border);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-normal);\n}\n.semantic-row {\n  background: none;\n  box-shadow: none;\n}\n.semantic-name {\n  font-size: var(--kb-type-body-lg);\n  font-weight: var(--kb-weight-medium);\n}\n.semantic-description {\n  margin-top: var(--kb-space-1);\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body);\n  font-weight: var(--kb-weight-regular);\n  line-height: var(--kb-leading-normal);\n}\n.semantic-list > .semantic-row {\n  border-bottom: 0;\n}\n.semantic-list > .semantic-row:has(~ .semantic-row:not([hidden])) {\n  border-bottom: var(--kb-stroke-xs) solid var(--kb-border);\n}\n.reference {\n  display: grid;\n  grid-template-columns: 1fr var(--kb-size-2xs);\n  gap: var(--kb-space-1) var(--kb-space-3);\n  width: 100%;\n  text-align: left;\n  border: 0;\n  padding: var(--kb-space-2-5) var(--kb-space-2);\n  margin: 0 var(--kb-bleed-row);\n  border-radius: var(--kb-radius-md);\n  font-size: var(--kb-type-body);\n  white-space: normal;\n}\n.reference:hover {\n  background: var(--kb-canvas);\n}\n.reference > span {\n  font-size: var(--kb-type-body-lg);\n  font-weight: var(--kb-weight-medium);\n}\n.reference small {\n  grid-column: 1;\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body-sm);\n  line-height: var(--kb-leading-normal);\n}\n.reference .icon {\n  grid-column: 2;\n  grid-row: 1;\n  color: var(--kb-text-muted);\n}\n.inline-reference {\n  display: inline;\n  border: 0;\n  padding: 0;\n  min-height: 0;\n  background: transparent;\n  color: var(--kb-text);\n  font: inherit;\n  text-align: left;\n  text-decoration: underline;\n  text-decoration-color: var(--kb-text-muted);\n  text-underline-offset: var(--kb-space-0-75);\n  white-space: normal;\n}\n.inline-reference:hover {\n  color: var(--kb-element);\n}\n.statement {\n  font-size: var(--kb-type-body-lg);\n  line-height: var(--kb-leading-loose);\n  margin: 0;\n}\n.relation-glyph {\n  display: flex;\n  align-items: center;\n  flex-wrap: wrap;\n  gap: var(--kb-space-1) var(--kb-space-3);\n  padding: var(--kb-space-2) 0 var(--kb-space-1);\n}\n.relation-glyph .inline-reference {\n  font-size: var(--kb-type-body-lg);\n  font-weight: var(--kb-weight-medium);\n}\n.glyph-target {\n  display: inline-flex;\n  align-items: center;\n  gap: var(--kb-space-3);\n}\n.glyph-wire {\n  width: var(--kb-size-sm);\n  height: var(--kb-icon-base);\n  flex: none;\n  overflow: visible;\n}\n.relation {\n  padding: var(--kb-space-1) 0;\n}\n.relation-block + .relation-block,\n.relation-block + .group,\n.group + .relation-block {\n  margin-top: var(--kb-space-5);\n}\n.relation-block > h3 {\n  margin: 0 0 var(--kb-space-3);\n  font-size: var(--kb-type-body-lg);\n}\n.relation-block > h3 .inline-reference {\n  text-decoration: none;\n}\n.conditions {\n  padding: var(--kb-space-2-5) var(--kb-space-3);\n  background: none;\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-loose);\n}\n.conditions > div {\n  display: flex;\n  flex-wrap: wrap;\n  gap: var(--kb-space-1-5) var(--kb-space-3);\n}\n.conditions strong {\n  font-weight: var(--kb-weight-medium);\n}\n.conjunction {\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-caption);\n}\n.frame-name {\n  display: inline-flex;\n  align-items: center;\n  gap: var(--kb-space-2);\n}\n.frame-name .icon {\n  width: var(--kb-icon-base);\n  height: var(--kb-icon-base);\n  color: var(--kb-frame);\n}\n.show-all {\n  display: block;\n  border: 0;\n  border-radius: var(--kb-radius-md);\n  background: transparent;\n  color: var(--kb-element);\n  font-size: var(--kb-type-button);\n  padding: var(--kb-space-2) var(--kb-space-2);\n  margin: var(--kb-space-1) var(--kb-bleed-row);\n}\n.show-all:hover {\n  background: var(--kb-canvas);\n}\n.source {\n  border-top: var(--kb-stroke-xs) solid var(--kb-border);\n  padding-top: var(--kb-space-4);\n  margin-top: var(--kb-space-5);\n  font-size: var(--kb-type-body-sm);\n  color: var(--kb-text-muted);\n}\n.source summary {\n  cursor: pointer;\n}\n.source pre {\n  white-space: pre-wrap;\n  overflow-wrap: anywhere;\n  font: var(--kb-type-caption) / var(--kb-leading-normal) var(--kb-font-mono);\n}\n.source code {\n  font: inherit;\n}\n.code-block {\n  position: relative;\n  margin-top: var(--kb-space-2);\n  padding: var(--kb-space-2) var(--kb-space-3);\n  background: var(--kb-canvas);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n}\n.code-block > button {\n  position: absolute;\n  top: var(--kb-space-1);\n  right: var(--kb-space-1);\n  padding: var(--kb-space-1);\n  border: var(--kb-stroke-xs) solid transparent;\n  border-radius: var(--kb-radius-sm);\n  background: none;\n  color: var(--kb-text-muted);\n}\n.code-block > button:hover,\n.code-block > button:focus-visible {\n  border-color: var(--kb-border);\n  background: var(--kb-surface);\n  color: var(--kb-text);\n}\n.meaning {\n  font-size: var(--kb-type-caption);\n  color: var(--kb-text-muted);\n  padding: 0 var(--kb-space-2) var(--kb-space-2);\n}\n.meaning summary {\n  cursor: pointer;\n}\n.guidance {\n  margin: var(--kb-space-5) 0 0;\n  padding: var(--kb-space-1) var(--kb-space-3);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-md);\n  font-size: var(--kb-type-body);\n  line-height: var(--kb-leading-normal);\n}\n.guidance summary {\n  cursor: pointer;\n  min-height: var(--kb-control-height);\n  padding: var(--kb-space-2) 0;\n}\n.guidance .claim:last-child {\n  border-bottom: 0;\n  padding-bottom: var(--kb-space-1);\n}\n\n.settings {\n  overflow-x: hidden;\n  right: var(--kb-overlay-clearance);\n  top: calc(var(--kb-size-lg) - var(--kb-space-2));\n  width: var(--kb-settings-width);\n  max-width: calc(100% - var(--kb-size-xs));\n  padding: var(--kb-space-3);\n  box-shadow: var(--kb-settings-box-shadow);\n  z-index: var(--kb-layer-over-everything);\n}\n.settings-head {\n  display: flex;\n  align-items: center;\n  gap: var(--kb-space-1-5);\n  min-height: var(--kb-size-sm);\n  margin-bottom: var(--kb-space-2-5);\n  font-size: var(--kb-type-body);\n}\n.settings-head strong {\n  font-weight: var(--kb-weight-medium);\n  flex: 1;\n}\n.settings button {\n  min-height: var(--kb-control-height);\n  padding: var(--kb-space-1) var(--kb-space-2);\n  border: 0;\n  border-radius: var(--kb-radius-md);\n  line-height: var(--kb-leading-tight);\n}\n.field {\n  margin: var(--kb-space-2-5) 0;\n}\n.field-label {\n  display: flex;\n  align-items: center;\n  gap: var(--kb-space-1-5);\n  font-size: var(--kb-type-body-sm);\n  color: var(--kb-text-muted);\n  margin-bottom: var(--kb-space-1-5);\n}\n.segment {\n  display: flex;\n  gap: var(--kb-space-0-75);\n  padding: var(--kb-space-0-75);\n  background: var(--kb-canvas);\n  border-radius: var(--kb-radius-lg);\n}\n.segment button {\n  flex: 1;\n  justify-content: center;\n  font-size: var(--kb-type-button);\n}\n.disclosure {\n  width: 100%;\n  font-size: var(--kb-type-body);\n  text-align: left;\n}\n.disclosure > span:first-of-type {\n  flex: 1;\n}\n.disclosure small {\n  font-size: var(--kb-type-body-sm);\n  color: var(--kb-text-muted);\n  max-width: var(--kb-disclosure-value-width);\n  text-align: right;\n}\n.divider {\n  height: var(--kb-divider-thickness);\n  background: var(--kb-border);\n  margin: var(--kb-space-2) 0;\n  border: 0;\n}\n.chips {\n  display: grid;\n  grid-template-columns: 1fr 1fr;\n  gap: var(--kb-space-1-5);\n}\n.chip {\n  min-width: 0;\n  overflow: hidden;\n  min-height: var(--kb-control-height);\n  padding: var(--kb-space-1) var(--kb-space-2);\n  font-size: var(--kb-type-button);\n  justify-content: flex-start;\n  text-align: left;\n  white-space: normal;\n  background: var(--kb-canvas);\n  box-shadow: var(--kb-chip-box-shadow);\n}\n.chip > span {\n  overflow: hidden;\n  text-overflow: ellipsis;\n}\n.chip .icon {\n  color: var(--kb-frame);\n}\n.chip[aria-pressed='true'] {\n  background: var(--kb-chip-pressed-background);\n  box-shadow: var(--kb-chip-pressed-box-shadow);\n}\n.hint {\n  font-size: var(--kb-type-body-sm);\n  line-height: var(--kb-leading-normal);\n  color: var(--kb-text-muted);\n  margin: var(--kb-space-2) 0 var(--kb-space-4);\n}\n.sample {\n  display: inline-flex;\n  align-items: center;\n  width: var(--kb-size-sm);\n  min-width: var(--kb-size-sm);\n  height: var(--kb-sample-height);\n  flex: none;\n  color: var(--kb-text);\n}\n.sample-endpoint {\n  width: var(--kb-sample-endpoint-width);\n  height: var(--kb-sample-endpoint-height);\n  border: var(--kb-stroke-xs) solid currentColor;\n  border-radius: var(--kb-radius-2xs);\n  flex: none;\n}\n.sample-connector {\n  height: 0;\n  flex: 1;\n  border-top: var(--kb-stroke-sm) solid currentColor;\n}\n.sample-badge {\n  font-size: var(--kb-sample-badge-text);\n  line-height: var(--kb-sample-badge-height);\n  border: var(--kb-stroke-xs) solid currentColor;\n  border-radius: var(--kb-radius-lg);\n  min-width: var(--kb-size-2xs);\n  text-align: center;\n}\n.stroke-sample {\n  width: var(--kb-size-xs);\n  border-top: var(--kb-stroke-xs) solid currentColor;\n}\n.stroke-sample[data-dashed='true'] {\n  border-top-style: dashed;\n}\n.stroke-stack {\n  display: flex;\n  flex-direction: column;\n  gap: var(--kb-space-1);\n}\n\n.search {\n  left: var(--kb-overlay-clearance);\n  top: calc(var(--kb-size-lg) - var(--kb-space-2));\n  width: var(--kb-size-2xl);\n  max-width: calc(100% - var(--kb-size-xs));\n}\n.search input {\n  width: 100%;\n  font: inherit;\n  color: var(--kb-text);\n  background: var(--kb-canvas);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  padding: var(--kb-space-2);\n  border-radius: var(--kb-radius-md);\n  margin-bottom: var(--kb-space-1);\n}\n.result {\n  width: 100%;\n  display: flex;\n  flex-direction: column;\n  align-items: flex-start;\n  gap: var(--kb-space-1);\n  padding: var(--kb-space-3) var(--kb-space-1);\n  border-bottom: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: 0;\n  text-align: left;\n  white-space: normal;\n}\n.result strong {\n  font-weight: var(--kb-weight-medium);\n}\n.muted {\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-body-sm);\n}\n\n.minimap {\n  right: var(--kb-space-4);\n  bottom: var(--kb-minimap-bottom);\n  width: var(--kb-size-xl);\n  padding: var(--kb-space-2-5);\n  box-shadow: var(--kb-lift-chrome);\n  border-radius: var(--kb-radius-lg);\n  max-height: none;\n}\n.minimap-head {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  margin-bottom: var(--kb-space-2);\n  cursor: grab;\n  touch-action: none;\n  user-select: none;\n  font-size: var(--kb-type-caption);\n}\n.minimap[data-dragging='true'] .minimap-head {\n  cursor: grabbing;\n}\n.minimap-head strong {\n  font-weight: var(--kb-weight-medium);\n}\n.plot {\n  display: block;\n  width: 100%;\n  height: var(--kb-plot-height);\n  background: var(--kb-canvas);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-sm);\n  touch-action: none;\n  cursor: crosshair;\n}\n.plot rect {\n  fill: var(--kb-frame);\n  opacity: var(--kb-plot-entity-opacity);\n}\n.plot rect[data-kind='artifact'] {\n  fill: var(--kb-artifact);\n}\n.plot rect[data-kind='element'] {\n  fill: var(--kb-element);\n}\n.plot rect[data-camera] {\n  fill: var(--kb-element);\n  fill-opacity: var(--kb-plot-camera-fill-opacity);\n  stroke: var(--kb-element);\n  stroke-width: var(--kb-plot-camera-stroke);\n  opacity: 1;\n  vector-effect: non-scaling-stroke;\n}\n.minimap-hint {\n  font-size: var(--kb-type-caption);\n  color: var(--kb-text-muted);\n  margin-top: var(--kb-space-1-5);\n}\n\n.overview {\n  left: var(--kb-overlay-clearance);\n  top: var(--kb-overlay-clearance);\n  width: var(--kb-overview-width);\n  max-width: calc(100% - var(--kb-size-xs));\n  z-index: var(--kb-layer-over-scrim);\n}\n.scrim {\n  position: absolute;\n  inset: 0;\n  background: var(--kb-scrim-background);\n  z-index: var(--kb-layer-over-panels);\n}\n.overview-head {\n  display: grid;\n  grid-template-columns: 1fr auto;\n  gap: var(--kb-space-1-5) var(--kb-space-3);\n  padding: var(--kb-space-3) var(--kb-space-4);\n}\n.overview-head > strong {\n  font-size: var(--kb-type-title);\n}\n.overview-head > .stats {\n  grid-column: 1 / -1;\n  padding: 0;\n  gap: var(--kb-space-1) var(--kb-space-3);\n}\n\n.share-menu {\n  position: absolute;\n  right: 0;\n  top: calc(100% + var(--kb-space-2));\n  width: var(--kb-size-xl);\n  padding: var(--kb-space-2);\n  background: var(--kb-surface);\n  border: var(--kb-stroke-xs) solid var(--kb-border);\n  border-radius: var(--kb-radius-2xl);\n  box-shadow: var(--kb-share-menu-box-shadow);\n  z-index: var(--kb-layer-over-everything);\n}\n.share-menu button {\n  width: 100%;\n  justify-content: flex-start;\n  gap: var(--kb-space-3);\n  white-space: normal;\n  text-align: left;\n}\n.menu-heading {\n  font-size: var(--kb-type-caption);\n  color: var(--kb-text-muted);\n  padding: var(--kb-space-2) var(--kb-space-2-5) var(--kb-space-1);\n}\n.share-menu small {\n  display: block;\n  color: var(--kb-text-muted);\n  font-size: var(--kb-type-caption);\n  margin-top: var(--kb-space-0-75);\n  font-weight: var(--kb-weight-regular);\n}\n\n.shell :is(.dock, .view-tabs, .settings, .sections, .share-menu, .utilities) button:hover {\n  background: var(--kb-control-hover-bg);\n  border-color: transparent;\n}\n.shell :is(.dock, .view-tabs, .settings, .sections, .share-menu, .utilities) button[aria-pressed='true'],\n.shell .dock button[aria-expanded='true'] {\n  background: var(--kb-control-selected-bg);\n  color: var(--kb-text);\n  border-color: transparent;\n  box-shadow: var(--kb-control-selected-ring);\n}\n.shell :is(.dock, .view-tabs, .settings, .sections, .share-menu, .utilities) button[aria-pressed='true']:hover,\n.shell .dock button[aria-expanded='true']:hover {\n  background: var(--kb-control-selected-hover-bg);\n}\n\n.empty {\n  position: absolute;\n  left: 50%;\n  top: 50%;\n  transform: translate(-50%, -50%);\n  color: var(--kb-text-muted);\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .shell button,\n  .card,\n  .card > *,\n  [data-connection],\n  [data-label],\n  [data-nub],\n  .wire {\n    transition: none;\n  }\n}\n@media (pointer: coarse) {\n  .shell :is(.dock, .view-tabs, .settings, .sections) button,\n  .shell .close {\n    min-height: var(--kb-size-md);\n  }\n}\n@container (max-width: 1050px) {\n  .topbar {\n    grid-template-columns: minmax(var(--kb-topbar-compact-identity-column), 1fr) auto minmax(var(--kb-topbar-utilities-column), 1fr);\n  }\n  .stats {\n    display: grid;\n    grid-template-columns: max-content max-content max-content;\n    gap: var(--kb-space-0-5) var(--kb-space-2-5);\n  }\n}\n@container (max-width: 740px) {\n  .topbar {\n    display: flex;\n    flex-wrap: wrap;\n    align-content: space-between;\n    min-height: var(--kb-topbar-narrow-height);\n    gap: var(--kb-space-3);\n  }\n  .identity {\n    width: 100%;\n    padding-right: var(--kb-identity-narrow-clearance);\n  }\n  .view-tabs {\n    order: 2;\n    margin: 0 auto;\n    display: grid;\n    grid-template-columns: 1fr 1fr 1fr;\n    max-width: 100%;\n  }\n  .view-tabs button {\n    white-space: normal;\n    line-height: var(--kb-leading-tight);\n    min-height: var(--kb-view-tabs-narrow-button-height);\n  }\n  .dock {\n    max-width: calc(100% - var(--kb-size-2xs));\n    bottom: var(--kb-space-2);\n    flex-wrap: wrap;\n    justify-content: center;\n  }\n  .panel {\n    max-height: min(var(--kb-panel-height-narrow-max), calc(100% * var(--kb-panel-height-narrow-fraction)));\n  }\n  .detail,\n  .search {\n    left: var(--kb-overlay-clearance);\n    width: calc(100% - var(--kb-overlay-clearance) * 2);\n  }\n  .minimap {\n    width: var(--kb-minimap-narrow-width);\n    bottom: var(--kb-minimap-narrow-bottom);\n  }\n  .legend {\n    bottom: var(--kb-legend-narrow-bottom);\n  }\n}\n";

  // styles/tokens.css
  var tokens_default = "/* Generated from visual-tokens.json. Do not edit. */\n.shell{\n  --kb-canvas: light-dark(#f5f5f1,#171e22);\n  --kb-surface: light-dark(#fff,#22292e);\n  --kb-text: light-dark(#263638,#e5eceb);\n  --kb-text-muted: light-dark(#617171,#a6b5b5);\n  --kb-border: light-dark(#d7dddf,#3b454c);\n  --kb-element: light-dark(#347773,#93c5bf);\n  --kb-artifact: light-dark(#8c6242,#dbaf87);\n  --kb-frame: light-dark(#736293,#b7a6d0);\n  --kb-accent: var(--kb-element);\n  --kb-focus: var(--kb-accent);\n  --kb-shadow-faint: #0001;\n  --kb-shadow-soft: #0002;\n  --kb-shadow-medium: #0003;\n  --kb-shadow-strong: #0004;\n  --kb-type-caption: 11px;\n  --kb-type-body-sm: 12px;\n  --kb-type-button: 12px;\n  --kb-type-body: 13px;\n  --kb-type-body-lg: 14px;\n  --kb-type-title: 17px;\n  --kb-font-sans: -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;\n  --kb-font-mono: ui-monospace,monospace;\n  --kb-space-1: 4px;\n  --kb-space-2: 8px;\n  --kb-space-3: 12px;\n  --kb-space-4: 16px;\n  --kb-space-5: 20px;\n  --kb-space-0-25: 1px;\n  --kb-space-0-5: 2px;\n  --kb-space-0-75: 3px;\n  --kb-space-1-5: 6px;\n  --kb-space-2-5: 10px;\n  --kb-bleed-row: -8px;\n  --kb-radius-2xs: 2px;\n  --kb-radius-xs: 3px;\n  --kb-radius-sm: 4px;\n  --kb-radius-md: 6px;\n  --kb-radius-lg: 8px;\n  --kb-radius-xl: 9px;\n  --kb-radius-2xl: 10px;\n  --kb-radius-3xl: 12px;\n  --kb-radius-4xl: 14px;\n  --kb-stroke-xs: 1px;\n  --kb-stroke-md: 2px;\n  --kb-stroke-lg: 3px;\n  --kb-stroke-sm: 1.5px;\n  --kb-leading-tight: 1.3;\n  --kb-leading-normal: 1.5;\n  --kb-leading-loose: 1.65;\n  --kb-icon-base: 16px;\n  --kb-lift-chrome: 0 4px 14px var(--kb-shadow-soft);\n  --kb-ground-frame: color-mix(in srgb,var(--kb-frame) 3%,var(--kb-canvas));\n  --kb-layer-under-map: -1;\n  --kb-layer-over-map: 3;\n  --kb-layer-over-viewport: 20;\n  --kb-layer-over-chrome: 30;\n  --kb-layer-over-everything: 60;\n  --kb-layer-over-panels: 40;\n  --kb-layer-over-scrim: 41;\n  --kb-opacity-disabled: .4;\n  --kb-opacity-dimmed: .13;\n  --kb-opacity-hushed: .5;\n  --kb-weight-medium: 500;\n  --kb-weight-regular: 400;\n  --kb-weight-emphasis: 600;\n  --kb-motion-camera: 420ms;\n  --kb-motion-glance: 140ms;\n  --kb-motion-hush: 160ms;\n  --kb-motion-dwell: 90ms;\n  --kb-size-2xs: 16px;\n  --kb-size-xs: 24px;\n  --kb-size-sm: 32px;\n  --kb-size-md: 40px;\n  --kb-size-lg: 90px;\n  --kb-size-xl: 220px;\n  --kb-size-2xl: 370px;\n  --kb-size-narrow-threshold: 740px;\n  --kb-zoom-step: 1.25;\n  --kb-zoom-growth-sm: 1;\n  --kb-zoom-growth-lg: 2;\n  --kb-control-height: 28px;\n  --kb-control-transition: background-color .12s,border-color .12s;\n  --kb-control-selected-bg: color-mix(in srgb,var(--kb-accent) 18%,var(--kb-surface));\n  --kb-control-selected-ring: inset 0 0 0 1px var(--kb-control-selected-border);\n  --kb-control-hover-bg: color-mix(in srgb,var(--kb-text) 7%,var(--kb-surface));\n  --kb-control-selected-hover-bg: color-mix(in srgb,var(--kb-accent) 25%,var(--kb-surface));\n  --kb-control-selected-border: color-mix(in srgb,var(--kb-accent) 48%,transparent);\n  --kb-overlay-clearance: 12px;\n  --kb-connection-rolled: light-dark(#99603b,#e4aa7f);\n  --kb-connection-stroke-nub: 1.5px;\n  --kb-connection-opacity-idle: 0.14;\n  --kb-connection-dash-situational: 7 5;\n  --kb-connection-dash-mixed: 12 3 3 3;\n  --kb-connection-stroke-base: 1px;\n  --kb-connection-stroke-selected: 2.5px;\n  --kb-connection-stroke-preview: 1.8px;\n  --kb-connection-stroke-leader: 0.7px;\n  --kb-connection-stroke-hit: 12px;\n  --kb-connection-opacity-label-faint: 0.08;\n  --kb-connection-opacity-normal: 0.5;\n  --kb-connection-label-height: 24px;\n  --kb-connection-label-baseline-offset: 4px;\n  --kb-connection-dash-frame: 4 3;\n  --kb-connection-count-size: 26px;\n  --kb-connection-label-padding: 16px;\n  --kb-scrim-background: #0008;\n  --kb-sample-badge-text: 10px;\n  --kb-sample-height: 20px;\n  --kb-sample-endpoint-width: 7px;\n  --kb-sample-endpoint-height: 10px;\n  --kb-sample-badge-height: 15px;\n  --kb-card-text: 15px;\n  --kb-card-rule-title-text: 21px;\n  --kb-card-selected-ring-element: 0 0 0 5px color-mix(in srgb,var(--kb-element) 12%,transparent);\n  --kb-card-selected-ring-artifact: 0 0 0 5px color-mix(in srgb,var(--kb-artifact) 12%,transparent);\n  --kb-card-selected-ring-frame: 0 0 0 5px color-mix(in srgb,var(--kb-frame) 12%,transparent);\n  --kb-card-selected-background-element: color-mix(in srgb,var(--kb-element) 15%,var(--kb-surface));\n  --kb-card-selected-background-frame: color-mix(in srgb,var(--kb-frame) 15%,var(--kb-surface));\n  --kb-card-border-artifact: color-mix(in srgb,var(--kb-artifact) 45%,var(--kb-border));\n  --kb-card-background-artifact: color-mix(in srgb,var(--kb-artifact) 5%,var(--kb-surface));\n  --kb-card-selected-background-artifact: color-mix(in srgb,var(--kb-artifact) 15%,var(--kb-surface));\n  --kb-card-rule-padding-x: 24px;\n  --kb-card-selected-background-option: color-mix(in srgb,var(--kb-frame) 12%,var(--kb-surface));\n  --kb-card-dimmed-border: color-mix(in srgb,var(--kb-border) 30%,var(--kb-canvas));\n  --kb-card-preview-glow-element: 0 0 7px color-mix(in srgb,var(--kb-element) 13%,transparent);\n  --kb-card-preview-glow-artifact: 0 0 7px color-mix(in srgb,var(--kb-artifact) 13%,transparent);\n  --kb-card-preview-glow-frame: 0 0 7px color-mix(in srgb,var(--kb-frame) 13%,transparent);\n  --kb-card-element-indent: 40px;\n  --kb-card-hover-filter: brightness(1.04);\n  --kb-card-frames-overflow-height: 17px;\n  --kb-card-frames-height: 18px;\n  --kb-identity-title-text: 16px;\n  --kb-identity-narrow-clearance: 78px;\n  --kb-panel-head-text: 18px;\n  --kb-panel-height-max: 480px;\n  --kb-panel-box-shadow: 0 12px 32px var(--kb-shadow-medium);\n  --kb-panel-height-fraction: 0.64;\n  --kb-panel-height-narrow-fraction: 0.4;\n  --kb-panel-height-narrow-max: 260px;\n  --kb-boundary-title-text: 22px;\n  --kb-boundary-caption-top: 28px;\n  --kb-boundary-scope-border: color-mix(in srgb,var(--kb-frame) 45%,var(--kb-border));\n  --kb-chip-pressed-box-shadow: inset 0 0 0 1px var(--kb-element);\n  --kb-chip-pressed-background: color-mix(in srgb,var(--kb-element) 12%,var(--kb-surface));\n  --kb-chip-box-shadow: inset 0 0 0 1px var(--kb-border);\n  --kb-minimap-bottom: 85px;\n  --kb-minimap-narrow-bottom: 150px;\n  --kb-minimap-clearance: 8px;\n  --kb-minimap-narrow-width: 166px;\n  --kb-share-menu-box-shadow: 0 12px 35px var(--kb-shadow-strong);\n  --kb-legend-bottom: 56px;\n  --kb-legend-narrow-bottom: 117px;\n  --kb-legend-swatch-width: 22px;\n  --kb-scene-margin: 24px;\n  --kb-view-tabs-box-shadow: 0 2px 8px var(--kb-shadow-faint);\n  --kb-view-tabs-narrow-button-height: 36px;\n  --kb-dock-box-shadow-2: 0 8px 24px var(--kb-shadow-soft);\n  --kb-settings-box-shadow: 0 12px 40px var(--kb-shadow-medium);\n  --kb-settings-width: 320px;\n  --kb-utility-control-size: 30px;\n  --kb-viewport-background: radial-gradient(var(--kb-border) .7px,transparent .7px) 0 0/24px 24px;\n  --kb-detail-width: 360px;\n  --kb-plot-entity-opacity: 0.65;\n  --kb-plot-height: 116px;\n  --kb-plot-camera-stroke: 1.5px;\n  --kb-plot-camera-fill-opacity: 0.14;\n  --kb-zoom-readout-width: 34px;\n  --kb-disclosure-value-width: 160px;\n  --kb-overview-width: 440px;\n  --kb-topbar-narrow-height: 132px;\n  --kb-topbar-compact-identity-column: 230px;\n  --kb-topbar-utilities-column: 85px;\n  --kb-facts-term-column: 95px;\n  --kb-active-dot-size: 5px;\n  --kb-divider-thickness: 1px;\n  --kb-label-char-width: 6.4px;\n  --kb-label-text: var(--kb-type-body-sm);\n  --kb-label-radius: var(--kb-radius-xs);\n  --kb-label-border: var(--kb-stroke-xs);\n  --kb-label-leader: var(--kb-connection-stroke-leader);\n  --kb-label-surface: var(--kb-canvas);\n  --kb-label-edge: var(--kb-border);\n  --kb-label-ink: var(--kb-text);\n  --kb-label-line: var(--kb-element);\n  --kb-label-zoom-growth: var(--kb-zoom-growth-lg);\n  --kb-count-size: var(--kb-connection-count-size);\n  --kb-count-gap: var(--kb-space-1-5);\n  --kb-count-text: var(--kb-type-body-sm);\n  --kb-count-radius: var(--kb-radius-2xl);\n  --kb-count-border: var(--kb-stroke-xs);\n  --kb-count-stroke: var(--kb-connection-stroke-nub);\n  --kb-count-inset: var(--kb-space-1);\n  --kb-count-surface: var(--kb-canvas);\n  --kb-count-edge: var(--kb-border);\n  --kb-count-ink: var(--kb-text);\n  --kb-count-line: var(--kb-element);\n  --kb-count-zoom-growth: var(--kb-zoom-growth-sm);\n  --kb-count-layer: var(--kb-layer-over-map);\n  --kb-heading-zoom-growth: var(--kb-zoom-growth-sm);\n  --kb-card-heading-zoom-growth: var(--kb-zoom-growth-sm);\n  --kb-card-heading-description-lines: 2;\n  --kb-card-heading-option-description-lines: 3;\n}\n";

  // src/lib/model.ts
  var DRAWABLE_PATH_DATA = /^[Mm][0-9eE,.\-+ \t]*[0-9][MmZzLlHhVvCcSsQqTtAa0-9,.\-+eE \t]*$/;
  var A_MONOGRAM_FITS_THE_ICON_BOX = /^[\p{L}\p{N}]{1,2}$/u;
  var drawable = (mark) => {
    const held = mark;
    if (typeof held.monogram === "string") return A_MONOGRAM_FITS_THE_ICON_BOX.test(held.monogram);
    return typeof held.glyph === "string" && DRAWABLE_PATH_DATA.test(held.glyph);
  };
  var aViewGroupsItsElements = (view) => view === "elements";
  var theDisplayAViewOpensOn = (view) => view === "elements" ? "counts" : "lines";
  var initialOptions = (view = "elements") => ({
    view,
    connections: "composition",
    display: theDisplayAViewOpensOn(view),
    lineStyle: "distinct",
    group: aViewGroupsItsElements(view),
    emphasis: [],
    frames: [],
    theme: "auto"
  });
  var emptySelection = () => ({ entity: "", connection: "", option: "" });
  var turningToLines = (current, patch) => patch.display === "lines" && current.display !== "lines" && patch.lineStyle === void 0;
  function updateOptions(current, patch) {
    const next = {
      ...current,
      ...patch,
      lineStyle: turningToLines(current, patch) ? "distinct" : patch.lineStyle ?? current.lineStyle,
      emphasis: [...patch.emphasis ?? current.emphasis],
      frames: [...patch.frames ?? current.frames]
    };
    const valid = ["frames", "artifacts", "elements"].includes(next.view) && ["", "relations", "composition"].includes(next.connections) && ["lines", "counts"].includes(next.display) && ["uniform", "distinct"].includes(next.lineStyle) && ["auto", "light", "dark"].includes(next.theme) && typeof next.group === "boolean" && next.emphasis.every((v) => typeof v === "string") && next.frames.every((v) => typeof v === "string");
    if (!valid) throw new Error("Invalid view options");
    return next;
  }
  function validateModel(input) {
    const model = input;
    if (!model || model.schema !== "knowledge-bus/explorer-model/1" || !Array.isArray(model.entities) || !Array.isArray(model.connections) || !Array.isArray(model.wiring) || !Array.isArray(model.rules) || !model.universe?.label || !model.source)
      throw new Error("Unsupported Explorer model");
    const ids = /* @__PURE__ */ new Set();
    for (const entity of model.entities) {
      if (typeof entity.id !== "string" || ids.has(entity.id) || typeof entity.label !== "string" || !["artifact", "element", "frame", "factor", "option"].includes(entity.kind) || !entity.raw || !entity.frameValues)
        throw new Error("Malformed Explorer entity");
      ids.add(entity.id);
    }
    const edges = /* @__PURE__ */ new Set();
    for (const c of model.connections) {
      if (edges.has(c.id) || !ids.has(c.from) || !ids.has(c.to) || typeof c.phrasing?.forward !== "string" || !c.phrasing.forward.trim() || c.ordered && (typeof c.phrasing.reverse !== "string" || !c.phrasing.reverse.trim()))
        throw new Error("Malformed Explorer connection");
      edges.add(c.id);
    }
    const ruleIds = new Set(model.rules.map((r) => r.id));
    for (const w of model.wiring)
      if (!ids.has(w.from) || !ids.has(w.to) && !ruleIds.has(w.to) || !Array.isArray(w.value)) throw new Error("Malformed Explorer wiring");
    if (model.guidance) {
      if (!Array.isArray(model.guidance.entries) || !Array.isArray(model.guidance.kinds)) throw new Error("Malformed Explorer guidance");
      const declaredKinds = new Set(model.guidance.kinds.map((k) => k.id));
      for (const entry of model.guidance.entries)
        if (!ids.has(entry.subject) || !declaredKinds.has(entry.kind) || typeof entry.claim !== "string" || !entry.claim.trim())
          throw new Error("Malformed Explorer guidance entry");
    }
    if (model.marks) {
      const declared = model.marks.declared;
      if (!declared || typeof declared !== "object" || Array.isArray(declared)) throw new Error("Malformed Explorer marks");
      for (const mark of Object.values(declared))
        if (!mark || typeof mark !== "object" || Object.keys(mark).length !== 1 || !drawable(mark))
          throw new Error("Malformed Explorer mark");
    }
    return model;
  }
  function phraseFor(c, subject) {
    if (subject !== c.from && subject !== c.to) throw new Error("Subject is not an endpoint");
    return c.ordered && subject === c.to ? c.phrasing.reverse : c.phrasing.forward;
  }
  var human = (s) => s ? s.replaceAll("-", " ").replace(/^./, (c) => c.toUpperCase()) : "";
  var relationKinds = (model) => model.source.relation_kinds ?? [];
  var compositionEntries = (model) => model.connections.filter((c) => c.kind === "composition").map((c) => ({ from: c.from, to: c.to, strength: c.strength, mode: c.mode, when: c.when, path: c.sourcePath }));
  var relationEdges = (model) => model.connections.filter((c) => c.kind !== "composition").map((c) => ({
    path: c.sourcePath,
    from: c.from,
    to: c.to,
    kind: c.kind,
    ordered: c.ordered,
    label: phraseFor(c, c.from),
    when: c.when
  }));
  var compositionLabel = (c) => c.strength === "core" ? c.when ? "Required when applicable" : "Required" : "When applicable";
  var compositionEdges = (model) => model.connections.filter((c) => c.kind === "composition").map((c) => ({
    path: c.sourcePath,
    from: c.from,
    to: c.to,
    kind: "composition",
    ordered: true,
    label: compositionLabel(c),
    strength: c.strength,
    mode: c.mode,
    when: c.when
  }));
  var wiringEdges = (model) => model.wiring.filter((w) => w.kind !== "ordering").map((w) => ({
    path: w.sourcePath,
    from: w.from,
    to: w.to,
    kind: w.kind,
    ordered: true,
    label: w.kind,
    value: w.value,
    targetPair: w.targetPair,
    targetLabel: w.targetLabel
  }));
  var byId = (model) => new Map(model.entities.map((e) => [e.id, e]));
  function referencedFrames(model, id) {
    const direct = model.wiring.filter((w) => w.kind !== "ordering" && (w.to === id || w.targetPair?.includes(id)));
    return [...new Set(direct.map((w) => w.sourceFrameId))];
  }

  // src/lib/rollup.ts
  function artifactEdges(source, composition, artifactIds, mode) {
    const artifacts = new Set(artifactIds);
    const members = /* @__PURE__ */ new Map();
    for (const entry of composition) {
      if (!members.has(entry.to)) members.set(entry.to, []);
      members.get(entry.to).push(entry);
    }
    const result = [];
    const add = (edge, from, to, via) => {
      if (from === to) return;
      result.push({
        ...edge,
        from,
        to,
        targetPair: void 0,
        rolled: via.length > 0,
        strength: via.some((x) => x.strength === "situational") ? "situational" : "core",
        provenance: { source: edge, composition: via },
        path: edge.path + "|" + from + "|" + to,
        label: edge.label + (via.length ? " · via " + [...new Set(via.map((x) => x.to))].join(", ") : "")
      });
    };
    if (mode === "composition") {
      for (const [, entries] of members)
        for (let i = 0; i < entries.length; i += 1)
          for (let j = i + 1; j < entries.length; j += 1)
            add(
              { path: entries[i].path + "|" + entries[j].path, label: "Shared element", ordered: false },
              entries[i].from,
              entries[j].from,
              [entries[i], entries[j]]
            );
    } else {
      for (const edge of source) {
        const left = artifacts.has(edge.from) ? [{ from: edge.from }] : members.get(edge.from) ?? [{ from: edge.from }];
        const right = artifacts.has(edge.to) ? [{ from: edge.to }] : members.get(edge.to) ?? [{ from: edge.to }];
        for (const a of left)
          for (const b of right)
            add(
              edge,
              a.from,
              b.from,
              [a, b].filter((x) => x.path)
            );
      }
    }
    const groups = /* @__PURE__ */ new Map();
    for (const edge of result) {
      const pair = edge.ordered ? [edge.from, edge.to] : [edge.from, edge.to].sort();
      const key = JSON.stringify([pair, edge.kind || mode, edge.rolled, edge.strength]);
      if (!groups.has(key)) groups.set(key, { ...edge, from: pair[0], to: pair[1], sources: [] });
      groups.get(key).sources.push(edge.provenance);
    }
    return [...groups.values()].map((e) => ({ ...e, label: e.label.split(" · ")[0] }));
  }
  function collapseCardPairs(edges) {
    const groups = /* @__PURE__ */ new Map();
    for (const edge of edges) {
      const key = JSON.stringify([edge.from, edge.to].sort());
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(edge);
    }
    return [...groups.entries()].map(([key, members]) => {
      const [from, to] = JSON.parse(key);
      const directions = new Set(members.filter((e) => e.ordered).map((e) => e.from === from ? "forward" : "reverse"));
      const mixedDirection = directions.size > 1 || members.some((e) => !e.ordered) && directions.size > 0;
      const labels = [...new Set(members.map((e) => e.label))].sort();
      const strengths = [...new Set(members.map((e) => e.strength))];
      const rolls = new Set(members.map((e) => e.rolled));
      const reverse = !mixedDirection && directions.has("reverse");
      return {
        ...members[0],
        from: reverse ? to : from,
        to: reverse ? from : to,
        path: "pair:" + key,
        label: labels.join(" · "),
        ordered: !mixedDirection && directions.size === 1,
        strength: strengths.length === 1 ? strengths[0] : "mixed",
        rolled: members.some((e) => e.rolled),
        mixedRollup: rolls.size > 1,
        members,
        sources: members.flatMap((e) => e.sources ?? [])
      };
    });
  }

  // src/lib/geometry.ts
  var union = (rects) => {
    if (!rects.length) return { x: 0, y: 0, w: 1, h: 1 };
    const x = Math.min(...rects.map((r) => r.x));
    const y = Math.min(...rects.map((r) => r.y));
    return { x, y, w: Math.max(...rects.map((r) => r.x + r.w)) - x, h: Math.max(...rects.map((r) => r.y + r.h)) - y };
  };
  var intersects = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  var contains = (outer, inner) => inner.x >= outer.x && inner.y >= outer.y && inner.x + inner.w <= outer.x + outer.w && inner.y + inner.h <= outer.y + outer.h;
  var expand = (r, by) => ({ x: r.x - by, y: r.y - by, w: r.w + by * 2, h: r.h + by * 2 });
  function polylineCrossings(lines) {
    const segments = lines.map((points) => points.slice(1).map((point, index) => ({ a: points[index], b: point })));
    const meeting = (s, t) => {
      const horizontal = s.a.y === s.b.y;
      if (horizontal === (t.a.y === t.b.y)) return null;
      const across = horizontal ? s : t;
      const down = horizontal ? t : s;
      const spans = (from, to, value) => value >= Math.min(from, to) && value <= Math.max(from, to);
      return spans(across.a.x, across.b.x, down.a.x) && spans(down.a.y, down.b.y, across.a.y) ? { x: down.a.x, y: across.a.y } : null;
    };
    const found = [];
    for (let i = 0; i < segments.length; i += 1)
      for (let j = i + 1; j < segments.length; j += 1)
        for (const first of segments[i])
          for (const second of segments[j]) {
            const point = meeting(first, second);
            if (point) found.push(point);
          }
    return found;
  }

  // src/lib/connected-layout.ts
  var COLUMNS = 5;
  var SLOT_X = 340;
  var SLOT_Y = 240;
  var ORIGIN_X = 60;
  var ORIGIN_Y = 70;
  var MAX_PASSES = 30;
  function connectedLayout(ids, edges) {
    const slots = ids.map((_, i) => ({ x: ORIGIN_X + i % COLUMNS * SLOT_X, y: ORIGIN_Y + Math.floor(i / COLUMNS) * SLOT_Y }));
    const order = [...ids].sort();
    const weights = /* @__PURE__ */ new Map();
    for (const e of edges) {
      if (e.from === e.to || !ids.includes(e.from) || !ids.includes(e.to)) continue;
      weights.set(JSON.stringify([e.from, e.to].sort()), 1);
    }
    const pairs = [...weights.keys()].map((k) => JSON.parse(k));
    const cost = () => {
      const pos = new Map(order.map((id, i) => [id, slots[i]]));
      return pairs.reduce((n, [a, b]) => n + Math.abs(pos.get(a).x - pos.get(b).x) + Math.abs(pos.get(a).y - pos.get(b).y), 0);
    };
    let score = cost();
    for (let pass = 0; pass < MAX_PASSES; pass += 1) {
      let best = score;
      let swap = null;
      for (let i2 = 0; i2 < order.length; i2 += 1)
        for (let j2 = i2 + 1; j2 < order.length; j2 += 1) {
          [order[i2], order[j2]] = [order[j2], order[i2]];
          const c = cost();
          [order[i2], order[j2]] = [order[j2], order[i2]];
          if (c < best) {
            best = c;
            swap = [i2, j2];
          }
        }
      if (!swap) break;
      const [i, j] = swap;
      [order[i], order[j]] = [order[j], order[i]];
      score = best;
    }
    return new Map(order.map((id, i) => [id, slots[i]]));
  }

  // src/lib/layout.ts
  var CARD_W = 230;
  var CARD_H = 104;
  var FRAME_CARD_W = 245;
  var FRAME_CARD_H = 150;
  var RULE_CARD_W = 410;
  var RULE_CARD_H = 118;
  var OPTION_CARD_W = 165;
  var OPTION_CARD_H = 166;
  var SECTION_X = 40;
  var SECTION_W = 1100;
  var FRAMES_BOUNDARY = "scope:frames";
  var EXCEPTIONS_BOUNDARY = "scope:rule";
  var FACTORS_BOUNDARY = "scope:factors";
  var FRAMES_CAPTION = "Your situation. These change what you need.";
  var EXCEPTIONS_CAPTION = "Your special cases. These mean no artifact is needed.";
  var FACTORS_CAPTION = "Your conditions. These shape how you go about the work.";
  var FACTORS_NONE_DECLARED = "This universe declares no factors.";
  var FRAME_CARDS_X = 85;
  var FRAME_CARDS_Y = 154;
  var FRAME_COLUMNS = 4;
  var FRAME_STEP_X = 265;
  var FRAME_STEP_Y = 170;
  var NESTED_X = 85;
  var NESTED_W = 1040;
  var ORDER_SCOPE_Y = 514;
  var ORDER_SCOPE_H = 223;
  var OPTIONS_X = 16;
  var OPTIONS_Y = 37;
  var OPTIONS_GAP = 12;
  var RULE_CARD_X = 130;
  var RULE_CARD_Y = 871;
  var FACTOR_Y = 1105;
  var FACTOR_H = 150;
  var FACTOR_COLUMNS = 4;
  var FACTOR_X = 20;
  var FACTOR_TOP = 45;
  var FACTOR_STEP_X = 265;
  var FACTOR_STEP_Y = 115;
  var FACTOR_CARD_H = 86;
  var NOTE_H = 72;
  var ARTIFACTS_X = 40;
  var ARTIFACTS_Y = 60;
  var ARTIFACT_COLUMNS = 9;
  var ARTIFACT_CARD_X = 30;
  var ARTIFACT_CARD_Y = 45;
  var ARTIFACT_STEP_X = 263;
  var ARTIFACT_STEP_Y = 136;
  var ARTIFACTS_W = 2420;
  var ARTIFACTS_H = 430;
  var ELEMENTS_Y = 560;
  var ELEMENTS_X = 0;
  var ELEMENTS_W = 3660;
  var ELEMENTS_H = 1900;
  var PHASE_COLUMNS = 3;
  var PHASE_X = 40;
  var PHASE_Y = 40;
  var PHASE_STEP_X = 1200;
  var PHASE_STEP_Y = 850;
  var PHASE_HEAD = 110;
  var PHASE_CARD_COLUMNS = 4;
  var PHASE_CARD_X = 30;
  var PHASE_CARD_Y = 90;
  var PHASE_CARD_STEP_X = 275;
  var PHASE_CARD_STEP_Y = 122;
  var FLAT_COLUMNS = 9;
  var FLAT_X = 40;
  var FLAT_Y = 60;
  var FLAT_STEP_X = 300;
  var FLAT_STEP_Y = 145;
  var CONNECTED_CARD_W = 230;
  var CONNECTED_CARD_H = 104;
  var GAP_BETWEEN_CARD_COLUMNS = PHASE_CARD_STEP_X - CARD_W;
  var GAP_BELOW_LAST_CARD_ROW = PHASE_HEAD + PHASE_CARD_STEP_Y - PHASE_CARD_Y - CARD_H;
  var sizeHolding = (box, held) => {
    const inside = union(held);
    return {
      w: Math.max(inside.x + inside.w + GAP_BETWEEN_CARD_COLUMNS, box.x + headingWidth(box)) - box.x,
      h: inside.y + inside.h + GAP_BELOW_LAST_CARD_ROW - box.y
    };
  };
  var sizedToHold = (box, held) => held.length ? { ...box, ...sizeHolding(box, held) } : box;
  var headDrop = (head) => head.caption ? CAPTION_DROP : TITLE_DROP;
  var placedToHold = (head, held) => {
    const inside = union(held);
    const origin = { x: inside.x - GAP_BETWEEN_CARD_COLUMNS, y: inside.y - headDrop(head) - GAP_BELOW_LAST_CARD_ROW };
    return { ...head, ...origin, ...sizeHolding({ ...head, ...origin }, held) };
  };
  var notingWhatTheUniverseDeclaresNoneOf = (box, text) => ({
    id: `${box.id}:none`,
    text,
    scopeId: box.id,
    x: box.x + GAP_BETWEEN_CARD_COLUMNS,
    y: box.y + headDrop(box) + GAP_BELOW_LAST_CARD_ROW,
    w: box.w - GAP_BETWEEN_CARD_COLUMNS * 2,
    h: NOTE_H
  });
  var drawingOnlyWhatSomethingDeclares = (cards, boundaries, notes) => {
    const declared = /* @__PURE__ */ new Set([...cards.map((c) => c.scopeId), ...notes.map((n) => n.scopeId)]);
    for (let growing = true; growing; ) {
      growing = false;
      for (const boundary of boundaries)
        if (declared.has(boundary.id) && boundary.scopeId && !declared.has(boundary.scopeId)) {
          declared.add(boundary.scopeId);
          growing = true;
        }
    }
    const drawn = boundaries.filter((b) => declared.has(b.id));
    return { cards, boundaries: drawn, notes, bounds: union([...cards, ...drawn]) };
  };
  function roleOfTheBoundaryEachCardStandsIn(layout) {
    const roleOf = new Map(layout.boundaries.map((boundary) => [boundary.id, boundary.role]));
    const standing = /* @__PURE__ */ new Map();
    for (const card of layout.cards) {
      const role = roleOf.get(card.scopeId);
      if (role) standing.set(card.id, role);
    }
    return standing;
  }
  function passesFrameFilter(model, id, filters) {
    if (!filters.length) return true;
    const referenced = (frame) => model.wiring.some((w) => w.sourceFrameId === frame && (w.to === id || w.targetPair?.includes(id)));
    const optionMatches = (frame, value) => model.wiring.some((w) => w.sourceFrameId === frame && (w.to === id || w.targetPair?.includes(id)) && w.value.includes(value));
    const groups = /* @__PURE__ */ new Map();
    for (const filter of filters) {
      const [kind, frame, ...rest] = filter.split(":");
      const key = kind === "option" ? "option:" + frame : filter;
      groups.set(key, [...groups.get(key) ?? [], kind === "option" ? rest.join(":") : ""]);
    }
    const entity = model.entities.find((e) => e.id === id);
    for (const [key, values] of groups) {
      const [kind, frame] = key.split(":");
      if (kind === "option") {
        const own = entity?.frameValues[frame];
        const matched = values.some(
          (value) => own === value || !!own && typeof own === "object" && Object.values(own).includes(value) || optionMatches(frame, value)
        );
        if (!matched) return false;
      } else if (!referenced(frame)) return false;
    }
    return true;
  }
  function orderingOptions(model) {
    const frame = model.entities.find((e) => e.id === model.orderingFrameId);
    return model.entities.filter((e) => e.kind === "option" && !!frame && e.id.startsWith("option:" + frame.sourceId + ":"));
  }
  function visibleElements(model, options) {
    return model.entities.filter((e) => e.kind === "element" && passesFrameFilter(model, e.id, options.frames));
  }
  function visibleArtifacts(model, options) {
    return model.entities.filter((e) => e.kind === "artifact" && passesFrameFilter(model, e.id, options.frames));
  }
  function framesLayout(model) {
    const cards = [];
    const insideFrames = [];
    const nested = [];
    const framed = model.entities.filter((e) => e.kind === "frame" && e.id !== model.orderingFrameId);
    framed.forEach((entity, index) => {
      const card = {
        id: entity.id,
        entity,
        kind: "frame",
        scopeId: FRAMES_BOUNDARY,
        x: FRAME_CARDS_X + index % FRAME_COLUMNS * FRAME_STEP_X,
        y: FRAME_CARDS_Y + Math.floor(index / FRAME_COLUMNS) * FRAME_STEP_Y,
        w: FRAME_CARD_W,
        h: FRAME_CARD_H
      };
      cards.push(card);
      insideFrames.push(card);
    });
    const ordering = model.entities.find((e) => e.id === model.orderingFrameId);
    const options = orderingOptions(model);
    if (ordering && options.length) {
      const orderScope = {
        id: model.orderingFrameId,
        title: ordering.label,
        caption: "",
        role: "scope",
        scopeId: FRAMES_BOUNDARY,
        x: NESTED_X,
        y: ORDER_SCOPE_Y,
        w: NESTED_W,
        h: ORDER_SCOPE_H
      };
      nested.push(orderScope);
      insideFrames.push(orderScope);
      const step = (NESTED_W - OPTIONS_X * 2 + OPTIONS_GAP) / options.length;
      options.forEach(
        (entity, index) => cards.push({
          id: entity.id,
          entity,
          kind: "option",
          scopeId: model.orderingFrameId,
          x: NESTED_X + OPTIONS_X + index * step,
          y: ORDER_SCOPE_Y + OPTIONS_Y,
          w: Math.min(OPTION_CARD_W, step - OPTIONS_GAP),
          h: OPTION_CARD_H
        })
      );
    }
    const rule = model.rules[0];
    if (rule) {
      const ruleCard = {
        id: rule.id,
        entity: null,
        kind: "rule",
        scopeId: EXCEPTIONS_BOUNDARY,
        x: RULE_CARD_X,
        y: RULE_CARD_Y,
        w: RULE_CARD_W,
        h: RULE_CARD_H
      };
      cards.push(ruleCard);
      const exceptions = placedToHold(
        { id: EXCEPTIONS_BOUNDARY, title: "Exceptions", caption: EXCEPTIONS_CAPTION, role: "section", scopeId: FRAMES_BOUNDARY },
        [ruleCard]
      );
      nested.push(exceptions);
      insideFrames.push(exceptions);
    }
    const boundaries = insideFrames.length ? [
      placedToHold({ id: FRAMES_BOUNDARY, title: "Frames", caption: FRAMES_CAPTION, role: "section", scopeId: "" }, insideFrames),
      ...nested
    ] : [];
    const factors = model.entities.filter((e) => e.kind === "factor");
    const factorCards = factors.map((entity, index) => ({
      id: entity.id,
      entity,
      kind: "factor",
      scopeId: FACTORS_BOUNDARY,
      x: SECTION_X + FACTOR_X + index % FACTOR_COLUMNS * FACTOR_STEP_X,
      y: FACTOR_Y + FACTOR_TOP + Math.floor(index / FACTOR_COLUMNS) * FACTOR_STEP_Y,
      w: CARD_W,
      h: FACTOR_CARD_H
    }));
    const factorsBox = {
      id: FACTORS_BOUNDARY,
      title: "Factors",
      caption: FACTORS_CAPTION,
      role: "section",
      scopeId: "",
      x: SECTION_X,
      y: FACTOR_Y,
      w: SECTION_W,
      h: FACTOR_H
    };
    const notes = factorCards.length ? [] : [notingWhatTheUniverseDeclaresNoneOf(factorsBox, FACTORS_NONE_DECLARED)];
    boundaries.push(sizedToHold(factorsBox, factorCards.length ? factorCards : notes));
    cards.push(...factorCards);
    return drawingOnlyWhatSomethingDeclares(cards, boundaries, notes);
  }
  function everyRolledPair(model, ids) {
    const composition = compositionEntries(model);
    const relations = relationEdges(model).filter((edge) => !edge.targetPair);
    const keys = /* @__PURE__ */ new Set();
    for (const mode of ["relations", "composition"])
      for (const edge of artifactEdges(mode === "relations" ? relations : [], composition, ids, mode))
        if (edge.from !== edge.to && ids.includes(edge.from) && ids.includes(edge.to)) keys.add([edge.from, edge.to].sort().join("\0"));
    return [...keys].map((key) => key.split("\0")).map(([from, to]) => ({ from, to }));
  }
  function artifactsLayout(model, options) {
    const artifacts = visibleArtifacts(model, options);
    const ids = artifacts.map((a) => a.id);
    const positions = connectedLayout(ids, everyRolledPair(model, ids));
    const cards = artifacts.map((entity) => {
      const p = positions.get(entity.id);
      return {
        id: entity.id,
        entity,
        kind: "artifact",
        scopeId: "scope:artifacts",
        x: p.x,
        y: p.y,
        w: CONNECTED_CARD_W,
        h: CONNECTED_CARD_H
      };
    });
    const boundaries = [
      placedToHold({ id: "scope:artifacts", title: "Artifacts", caption: "", role: "section", scopeId: "" }, cards)
    ];
    return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
  }
  function elementsLayout(model, options) {
    const cards = [];
    const boundaries = [];
    const artifacts = visibleArtifacts(model, options);
    const artifactCards = artifacts.map((entity, index) => ({
      id: entity.id,
      entity,
      kind: "artifact",
      scopeId: "scope:artifacts",
      x: ARTIFACTS_X + ARTIFACT_CARD_X + index % ARTIFACT_COLUMNS * ARTIFACT_STEP_X,
      y: ARTIFACTS_Y + ARTIFACT_CARD_Y + Math.floor(index / ARTIFACT_COLUMNS) * ARTIFACT_STEP_Y,
      w: CARD_W,
      h: CARD_H
    }));
    const artifactsBox = sizedToHold(
      {
        id: "scope:artifacts",
        title: "Artifacts",
        caption: "",
        role: "section",
        scopeId: "",
        x: ARTIFACTS_X,
        y: ARTIFACTS_Y,
        w: ARTIFACTS_W,
        h: ARTIFACTS_H
      },
      artifactCards
    );
    boundaries.push(artifactsBox);
    cards.push(...artifactCards);
    const elements = visibleElements(model, options);
    const elementsTop = artifactsBox.y + artifactsBox.h + (ELEMENTS_Y - ARTIFACTS_Y - artifactsBox.h > 0 ? ELEMENTS_Y - artifactsBox.y - artifactsBox.h : PHASE_Y);
    if (!options.group) {
      const flatCards = elements.map((entity, index) => ({
        id: entity.id,
        entity,
        kind: "element",
        scopeId: "scope:elements",
        x: FLAT_X + index % FLAT_COLUMNS * FLAT_STEP_X,
        y: elementsTop + FLAT_Y + Math.floor(index / FLAT_COLUMNS) * FLAT_STEP_Y,
        w: CARD_W,
        h: CARD_H
      }));
      boundaries.push(
        sizedToHold(
          {
            id: "scope:elements",
            title: "Elements",
            caption: "",
            role: "section",
            scopeId: "",
            x: ELEMENTS_X,
            y: elementsTop,
            w: ELEMENTS_W,
            h: ELEMENTS_H
          },
          flatCards
        )
      );
      cards.push(...flatCards);
      return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
    }
    const ordering = model.orderingFrameId.split(":").slice(1).join(":");
    const options_ = orderingOptions(model);
    const groups = options_.map((option) => ({
      option,
      members: elements.filter((e) => (e.frameValues[ordering] ?? e.raw[ordering]) === option.sourceId)
    })).filter((group) => group.members.length);
    const groupBoxes = [];
    groups.forEach((group, index) => {
      const x = PHASE_X + index % PHASE_COLUMNS * PHASE_STEP_X;
      const y = elementsTop + PHASE_Y + Math.floor(index / PHASE_COLUMNS) * PHASE_STEP_Y;
      const members = group.members.map((entity, member) => ({
        id: entity.id,
        entity,
        kind: "element",
        scopeId: group.option.id,
        x: x + PHASE_CARD_X + member % PHASE_CARD_COLUMNS * PHASE_CARD_STEP_X,
        y: y + PHASE_CARD_Y + Math.floor(member / PHASE_CARD_COLUMNS) * PHASE_CARD_STEP_Y,
        w: CARD_W,
        h: CARD_H
      }));
      const head = { title: group.option.label, caption: group.option.description, x, y };
      groupBoxes.push({ id: group.option.id, role: "group", scopeId: "scope:elements", ...head, ...sizeHolding(head, members) });
      cards.push(...members);
    });
    boundaries.push(
      sizedToHold(
        {
          id: "scope:elements",
          title: "Elements",
          caption: "",
          role: "section",
          scopeId: "",
          x: ELEMENTS_X,
          y: elementsTop,
          w: ELEMENTS_W,
          h: ELEMENTS_H
        },
        groupBoxes
      ),
      ...groupBoxes
    );
    return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
  }
  function layoutFor(model, options) {
    if (options.view === "frames") return framesLayout(model);
    if (options.view === "artifacts") return artifactsLayout(model, options);
    return elementsLayout(model, options);
  }
  var TITLE_RISE = 20;
  var TITLE_DROP = 22;
  var CAPTION_DROP = 56;
  var HEAD_INSET = 21;
  var TITLE_GLYPH = 30;
  var TITLE_CHAR = 16.5;
  var CAPTION_CHAR = 8.2;
  function headingWidth(head) {
    return HEAD_INSET + Math.max(TITLE_GLYPH + head.title.length * TITLE_CHAR, head.caption.length * CAPTION_CHAR);
  }
  var boundaryHeads = (layout) => layout.boundaries.map((b) => ({
    x: b.x,
    y: b.y - TITLE_RISE,
    w: Math.min(b.w, headingWidth(b)),
    h: TITLE_RISE + (b.caption ? CAPTION_DROP : TITLE_DROP)
  }));
  var cardRects = (layout) => new Map(layout.cards.map((c) => [c.id, { x: c.x, y: c.y, w: c.w, h: c.h }]));

  // src/lib/routing.ts
  var PORT_SPREAD = 7;
  var PORT_STEP = 4;
  var BASE_GAP = 20;
  var CORNER_COST = 18;
  var CONGESTION_TOLERANCE = 9;
  var CONGESTION_WEIGHT = 8;
  var LABEL_CHAR = 8;
  var LABEL_PADDING = 24;
  var LABEL_PENALTY = 400;
  var HASH_MULTIPLIER = 31;
  var Router = class {
    routed = [];
    begin() {
      this.routed = [];
    }
    path(a, b, rects, edge = {}) {
      const identity = [edge.from, edge.to, edge.kind, edge.strength].join("|");
      const hash = [...identity].reduce((n, c) => n * HASH_MULTIPLIER + c.charCodeAt(0) >>> 0, 0);
      const offset = (hash % PORT_SPREAD - (PORT_SPREAD - 1) / 2) * PORT_STEP;
      const gap = BASE_GAP + offset;
      const boxes = [...rects.values()].filter((r) => r.w > 0 && r.h > 0);
      const ports = (r) => [
        [
          { x: r.x + r.w / 2 + offset, y: r.y },
          { x: r.x + r.w / 2 + offset, y: r.y - gap }
        ],
        [
          { x: r.x + r.w, y: r.y + r.h / 2 + offset },
          { x: r.x + r.w + gap, y: r.y + r.h / 2 + offset }
        ],
        [
          { x: r.x + r.w / 2 + offset, y: r.y + r.h },
          { x: r.x + r.w / 2 + offset, y: r.y + r.h + gap }
        ],
        [
          { x: r.x, y: r.y + r.h / 2 + offset },
          { x: r.x - gap, y: r.y + r.h / 2 + offset }
        ]
      ];
      const clear = (p, q) => !boxes.some(
        (r) => p.x === q.x ? p.x > r.x && p.x < r.x + r.w && Math.max(p.y, q.y) > r.y && Math.min(p.y, q.y) < r.y + r.h : p.y > r.y && p.y < r.y + r.h && Math.max(p.x, q.x) > r.x && Math.min(p.x, q.x) < r.x + r.w
      );
      const xs = [...new Set(boxes.flatMap((r) => [r.x - gap, r.x + r.w + gap]))].sort((x, y) => x - y);
      const ys = [...new Set(boxes.flatMap((r) => [r.y - gap, r.y + r.h + gap]))].sort((x, y) => x - y);
      const found = { points: [], score: Infinity };
      const overlap = (lowA, highA, lowB, highB) => Math.max(0, Math.min(highA, highB) - Math.max(lowA, lowB));
      const consider = (candidate) => {
        const points = candidate.filter((p, i) => !i || p.x !== candidate[i - 1].x || p.y !== candidate[i - 1].y);
        if (points.some((p, i) => i && !clear(points[i - 1], p))) return;
        const congestion = points.reduce((sum, q, i) => {
          if (!i) return sum;
          const p = points[i - 1];
          return sum + this.routed.reduce((n, [u, v]) => {
            if (p.x === q.x && u.x === v.x && Math.abs(p.x - u.x) < CONGESTION_TOLERANCE)
              return n + overlap(Math.min(p.y, q.y), Math.max(p.y, q.y), Math.min(u.y, v.y), Math.max(u.y, v.y)) * CONGESTION_WEIGHT;
            if (p.y === q.y && u.y === v.y && Math.abs(p.y - u.y) < CONGESTION_TOLERANCE)
              return n + overlap(Math.min(p.x, q.x), Math.max(p.x, q.x), Math.min(u.x, v.x), Math.max(u.x, v.x)) * CONGESTION_WEIGHT;
            return n;
          }, 0);
        }, 0);
        const labelWidth = (edge.label || "").length * LABEL_CHAR + LABEL_PADDING;
        const labelRoom = points.some((p, i) => i && p.y === points[i - 1].y && Math.abs(p.x - points[i - 1].x) >= labelWidth);
        const length = points.reduce((n, p, i) => n + (i ? Math.abs(p.x - points[i - 1].x) + Math.abs(p.y - points[i - 1].y) : 0), 0) + points.length * CORNER_COST + congestion + (labelRoom ? 0 : LABEL_PENALTY);
        if (length < found.score) {
          found.score = length;
          found.points = points;
        }
      };
      for (const [start, p] of ports(a))
        for (const [end, q] of ports(b)) {
          for (const x of xs) consider([start, p, { x, y: p.y }, { x, y: q.y }, q, end]);
          for (const y of ys) consider([start, p, { x: p.x, y }, { x: q.x, y }, q, end]);
        }
      const chosen = found.points;
      const path = chosen.length ? "M " + chosen.map((p) => `${p.x} ${p.y}`).join(" L ") : `M ${a.x + a.w / 2} ${a.y + a.h} L ${a.x + a.w / 2} ${b.y - BASE_GAP} L ${b.x + b.w / 2} ${b.y - BASE_GAP} L ${b.x + b.w / 2} ${b.y}`;
      const segments = chosen.slice(1).map((p, i) => [chosen[i], p]);
      this.routed.push(...segments);
      return path;
    }
  };

  // src/lib/bundles.ts
  function bundleFocusCard(selected, hover, kind, connection) {
    if (selected) return selected;
    if (connection.startsWith("bundle:")) return JSON.parse(connection.slice(7))[0];
    return connection || kind ? "" : hover;
  }
  function bundleExpandedPairs(source, id) {
    if (!id) return source;
    const groups = /* @__PURE__ */ new Map();
    for (const edge of source) {
      if (edge.targetPair || edge.from === edge.to || edge.from !== id && edge.to !== id) continue;
      const other = edge.from === id ? edge.to : edge.from;
      if (!groups.has(other)) groups.set(other, []);
      groups.get(other).push(edge);
    }
    const replacements = /* @__PURE__ */ new Map();
    const removed = /* @__PURE__ */ new Set();
    for (const [other, members] of groups) {
      if (members.length < 2) continue;
      const [bundle] = collapseCardPairs(members.map((edge) => ({ ...edge, sources: [{ source: edge, composition: [] }] })));
      bundle.path = "bundle:" + JSON.stringify([id, other]);
      bundle.bundled = true;
      replacements.set(members[0], bundle);
      members.slice(1).forEach((edge) => removed.add(edge));
    }
    return source.filter((edge) => !removed.has(edge)).map((edge) => replacements.get(edge) ?? edge);
  }

  // styles/visual-tokens.json
  var visual_tokens_default = {
    version: 2,
    scope: ".shell",
    roles: {
      color: {
        canvas: {
          kind: "color",
          value: "light-dark(#f5f5f1,#171e22)",
          role: "Canvas and recessed controls"
        },
        surface: {
          kind: "color",
          value: "light-dark(#fff,#22292e)",
          role: "Cards, menus and detail surfaces"
        },
        text: {
          kind: "color",
          value: "light-dark(#263638,#e5eceb)",
          role: "Primary readable content"
        },
        "text-muted": {
          kind: "color",
          value: "light-dark(#617171,#a6b5b5)",
          role: "Secondary descriptions and metadata"
        },
        border: {
          kind: "color",
          value: "light-dark(#d7dddf,#3b454c)",
          role: "Surface boundaries and dividers"
        },
        element: {
          kind: "color",
          value: "light-dark(#347773,#93c5bf)",
          role: "Element identity; legacy direct-connection and UI accent route"
        },
        artifact: {
          kind: "color",
          value: "light-dark(#8c6242,#dbaf87)",
          role: "Artifact identity"
        },
        frame: {
          kind: "color",
          value: "light-dark(#736293,#b7a6d0)",
          role: "Frame and factor identity"
        },
        accent: {
          kind: "color",
          value: "var(--kb-element)",
          role: "Current control accent; independent route for later overhaul"
        },
        focus: {
          kind: "color",
          value: "var(--kb-accent)",
          role: "Keyboard focus"
        },
        "shadow-faint": {
          kind: "color",
          value: "#0001",
          role: "Faint elevation"
        },
        "shadow-soft": {
          kind: "color",
          value: "#0002",
          role: "Light elevation"
        },
        "shadow-medium": {
          kind: "color",
          value: "#0003",
          role: "Popover elevation"
        },
        "shadow-strong": {
          kind: "color",
          value: "#0004",
          role: "Strong popover elevation"
        }
      },
      type: {
        caption: {
          kind: "length",
          value: "11px",
          role: "Caption — stats, legend keys, metadata and code snippets"
        },
        "body-sm": {
          kind: "length",
          value: "12px",
          role: "Small body — card subtitles, hints and field labels"
        },
        button: {
          kind: "length",
          value: "12px",
          role: "Control label — dock, view tabs, chips and segmented buttons"
        },
        body: {
          kind: "length",
          value: "13px",
          role: "Body — the board default reading size"
        },
        "body-lg": {
          kind: "length",
          value: "14px",
          role: "Large body — element and option card titles, section paragraphs and statements"
        },
        title: {
          kind: "length",
          value: "17px",
          role: "Heading — scope boundary titles, detail questions and the overview title"
        }
      },
      font: {
        sans: {
          kind: "font",
          value: "-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif",
          role: "Interface font stack"
        },
        mono: {
          kind: "font",
          value: "ui-monospace,monospace",
          role: "Raw source snippets"
        }
      },
      space: {
        "1": {
          kind: "length",
          value: "4px",
          role: "Small control padding, and the gap inside dock, result, search and stat rows, chips, the legend and utilities"
        },
        "2": {
          kind: "length",
          value: "8px",
          role: "Standard gap and padding across the dock, panels, menus, buttons, card footers, dividers and the search field"
        },
        "3": {
          kind: "length",
          value: "12px",
          role: "Card padding on the map, panel, overview and top bar padding, and the gap between fact and condition rows"
        },
        "4": {
          kind: "length",
          value: "16px",
          role: "Panel body and overview head padding, top bar side padding, and the board edge inset for the dock, legend and minimap"
        },
        "5": {
          kind: "length",
          value: "20px",
          role: "Boundary title and caption inset from the boundary edge, section padding, and rule card and source block padding"
        },
        base: 4,
        fineWork: [1, 2, 3, 6, 10],
        "0-25": {
          kind: "length",
          value: "1px",
          role: "Hairline gap between the rails of the view tabs and the dock groups"
        },
        "0-5": {
          kind: "length",
          value: "2px",
          role: "Tightest gap: selected card outline offset, section list and stat rows"
        },
        "0-75": {
          kind: "length",
          value: "3px",
          role: "Focus ring offset, and the tightest gap inside cards, the dock, segments and stats"
        },
        "1-5": {
          kind: "length",
          value: "6px",
          role: "Gap between paired items: chips, utilities, condition rows, card stats and count badges"
        },
        "2-5": {
          kind: "length",
          value: "10px",
          role: "Panel head and body padding, and the gap inside entries, fields, minimap and stats"
        }
      },
      bleed: {
        row: {
          kind: "length",
          value: "-8px",
          role: "Negative inset pulling reference rows and the show-all row out to their panel edge"
        }
      },
      radius: {
        "2xs": {
          kind: "length",
          value: "2px",
          role: "Connection sample endpoint — corner"
        },
        xs: {
          kind: "length",
          value: "3px",
          role: "Connection label — corner, on the map and in the SVG export"
        },
        sm: {
          kind: "length",
          value: "4px",
          role: "Minimap plot — corner"
        },
        md: {
          kind: "length",
          value: "6px",
          role: "The one button and card corner: every card, every button, pills, references, conditions and the search field"
        },
        lg: {
          kind: "length",
          value: "8px",
          role: "Corner of the minimap, the legend, the segmented control, the view tab rail and the sample badge"
        },
        xl: {
          kind: "length",
          value: "9px",
          role: "Corner of the dock rail and the card frame overflow pill"
        },
        "2xl": {
          kind: "length",
          value: "10px",
          role: "Corner of rule cards, the share menu and the connection count badge"
        },
        "3xl": {
          kind: "length",
          value: "12px",
          role: "Corner of floating panels"
        },
        "4xl": {
          kind: "length",
          value: "14px",
          role: "Corner of frame boundaries, on the map and in the SVG export"
        }
      },
      stroke: {
        xs: {
          kind: "length",
          value: "1px",
          role: "Hairline border on cards, panels, controls and the connection count badge"
        },
        md: {
          kind: "length",
          value: "2px",
          role: "Selected card border, focus ring and legend swatch"
        },
        lg: {
          kind: "length",
          value: "3px",
          role: "Kind accent bar down the left edge of a card, on the map and in the SVG export"
        },
        sm: {
          kind: "length",
          value: "1.5px",
          role: "Icon stroke, and the connector drawn in the connection sample"
        }
      },
      leading: {
        tight: {
          kind: "number",
          value: "1.3",
          role: "Leading for tight two-line labels: rule card titles, panel headings, settings buttons and view tabs"
        },
        normal: {
          kind: "number",
          value: "1.5",
          role: "Leading the board sets as its default, and the leading of running copy: card subtitles, captions, facts, hints, section paragraphs, stats and code"
        },
        loose: {
          kind: "number",
          value: "1.65",
          role: "Leading for statements and condition lists"
        }
      },
      icon: {
        base: {
          kind: "length",
          value: "16px",
          role: "Icon size on the map and in the SVG export: board controls, card titles, card frames, option cards and the frame name"
        }
      },
      lift: {
        chrome: {
          kind: "shadow",
          value: "0 4px 14px var(--kb-shadow-soft)",
          role: "Chrome that floats over the map, clear of it without resting on it"
        }
      },
      ground: {
        frame: {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-frame) 3%,var(--kb-canvas))",
          role: "Ground of a frame or one of its values — the wash its boundary lays on the map, and what a dimmed card standing on it paints to stay level with it"
        }
      },
      layer: {
        "under-map": {
          kind: "number",
          value: "-1",
          role: "Boundary ground, beneath the wires, count badges and cards the map draws on top of it"
        },
        "over-map": {
          kind: "number",
          value: "3",
          role: "Legend and inset count badge, each above the map it sits on"
        },
        "over-viewport": {
          kind: "number",
          value: "20",
          role: "Top bar and dock"
        },
        "over-chrome": {
          kind: "number",
          value: "30",
          role: "Detail, search and minimap panels"
        },
        "over-everything": {
          kind: "number",
          value: "60",
          role: "View options and share menus"
        },
        "over-panels": {
          kind: "number",
          value: "40",
          role: "Backdrop dimming the board behind an overlay"
        },
        "over-scrim": {
          kind: "number",
          value: "41",
          role: "Universe overview above its backdrop"
        }
      },
      opacity: {
        disabled: {
          kind: "number",
          value: ".4",
          role: "Disabled control opacity"
        },
        dimmed: {
          kind: "number",
          value: ".13",
          role: "Opacity of the contents of a dimmed card"
        },
        hushed: {
          kind: "number",
          value: ".5",
          role: "Opacity of the contents of a hushed card"
        }
      },
      weight: {
        medium: {
          kind: "number",
          value: "500",
          role: "Weight for titles and headings across the map and the panels"
        },
        regular: {
          kind: "number",
          value: "400",
          role: "Weight returning share menu help text to normal"
        },
        emphasis: {
          kind: "number",
          value: "600",
          role: "Weight for the title of a selected card"
        }
      },
      motion: {
        camera: {
          kind: "duration",
          value: "420ms",
          role: "Selection and overview camera transition; cubic ease-out remains behavior"
        },
        glance: {
          kind: "duration",
          value: "140ms",
          role: "Ease of the one thing under the pointer as it lights"
        },
        hush: {
          kind: "duration",
          value: "160ms",
          role: "Ease of the board as its emphasis changes"
        },
        dwell: {
          kind: "duration",
          value: "90ms",
          role: "Rest the pointer must take before the board follows it"
        }
      },
      size: {
        "2xs": {
          kind: "length",
          value: "16px",
          role: "Reference chevron column, sample badge minimum width, and the dock side margin when it wraps"
        },
        xs: {
          kind: "length",
          value: "24px",
          role: "Side margin overlays leave at the viewport edge, and the width of the stroke sample"
        },
        sm: {
          kind: "length",
          value: "32px",
          role: "Settings header height and the width of the connection sample"
        },
        md: {
          kind: "length",
          value: "40px",
          role: "Coarse-pointer minimum target height for board controls and the close button"
        },
        lg: {
          kind: "length",
          value: "90px",
          role: "Top bar height, which the search and settings panels hang beneath"
        },
        xl: {
          kind: "length",
          value: "220px",
          role: "Minimap and share menu width"
        },
        "2xl": {
          kind: "length",
          value: "370px",
          role: "Search panel width and the top bar identity column minimum"
        },
        "narrow-threshold": {
          kind: "length",
          value: "740px",
          role: "Narrow layout threshold, matching the container query"
        }
      },
      zoom: {
        step: {
          kind: "number",
          value: "1.25",
          role: "One click of the zoom control, the factor every zoom growth is counted in"
        },
        "growth-sm": {
          kind: "number",
          value: "1",
          role: "Count badges and boundary headings grow by one zoom click as the camera zooms out"
        },
        "growth-lg": {
          kind: "number",
          value: "2",
          role: "Connection labels grow by two zoom clicks as the camera zooms out"
        }
      },
      control: {
        height: {
          kind: "length",
          value: "28px",
          role: "Compact pointer control height"
        },
        transition: {
          kind: "transition",
          value: "background-color .12s,border-color .12s",
          role: "Ease a control applies to its background and border when its state changes"
        },
        "selected-bg": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-accent) 18%,var(--kb-surface))",
          role: "Pressed control — background"
        },
        "selected-ring": {
          kind: "shadow",
          value: "inset 0 0 0 1px var(--kb-control-selected-border)",
          role: "Pressed or open control — inner ring"
        },
        "hover-bg": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-text) 7%,var(--kb-surface))",
          role: "Hovered control — background"
        },
        "selected-hover-bg": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-accent) 25%,var(--kb-surface))",
          role: "Hovered pressed control — background"
        },
        "selected-border": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-accent) 48%,transparent)",
          role: "Persistent control selection border"
        }
      },
      overlay: {
        clearance: {
          kind: "length",
          value: "12px",
          role: "Detail surface clearance from viewport"
        }
      },
      connection: {
        rolled: {
          kind: "color",
          value: "light-dark(#99603b,#e4aa7f)",
          role: "Rolled-up connection identity"
        },
        "stroke-nub": {
          kind: "length",
          value: "1.5px",
          role: "Count connector stroke"
        },
        "opacity-idle": {
          kind: "number",
          value: "0.14",
          role: "Idle connection opacity"
        },
        "dash-situational": {
          kind: "number",
          value: "7 5",
          role: "Situational connector dash pattern"
        },
        "dash-mixed": {
          kind: "number",
          value: "12 3 3 3",
          role: "Mixed-strength connector dash pattern"
        }
      }
    },
    parts: {
      connection: {
        selectors: [".wire", ".arrowhead"],
        "stroke-base": {
          kind: "length",
          value: "1px",
          role: "Normal connection stroke"
        },
        "stroke-selected": {
          kind: "length",
          value: "2.5px",
          role: "Selected connection stroke"
        },
        "stroke-preview": {
          kind: "length",
          value: "1.8px",
          role: "Preview connection stroke"
        },
        "stroke-leader": {
          kind: "length",
          value: "0.7px",
          role: "Label leader stroke"
        },
        "stroke-hit": {
          kind: "length",
          value: "12px",
          role: "Connection hit target width"
        },
        "opacity-label-faint": {
          kind: "number",
          value: "0.08",
          role: "Unrelated label opacity"
        },
        "opacity-normal": {
          kind: "number",
          value: "0.5",
          role: "Unselected map connection opacity"
        },
        "label-height": {
          kind: "length",
          value: "24px",
          role: "Connection label line box"
        },
        "label-baseline-offset": {
          kind: "length",
          value: "4px",
          role: "Drop from the centre of a label or count badge to its text baseline in the SVG export"
        },
        "dash-frame": {
          kind: "number",
          value: "4 3",
          role: "Frame connector dash pattern"
        },
        "count-size": {
          kind: "length",
          value: "26px",
          role: "Connection count badge size"
        },
        "label-padding": {
          kind: "length",
          value: "16px",
          role: "Combined horizontal label padding"
        }
      },
      scrim: {
        selectors: [".scrim"],
        background: {
          kind: "color",
          value: "#0008",
          role: "Universe overlay backdrop"
        }
      },
      sample: {
        selectors: [".sample"],
        "badge-text": {
          kind: "length",
          value: "10px",
          role: "Connection sample badge — count digit in the display menu"
        },
        height: {
          kind: "length",
          value: "20px",
          role: "Connection sample — row height"
        },
        "endpoint-width": {
          kind: "length",
          value: "7px",
          role: "Connection sample — endpoint width"
        },
        "endpoint-height": {
          kind: "length",
          value: "10px",
          role: "Connection sample — endpoint height"
        },
        "badge-height": {
          kind: "length",
          value: "15px",
          role: "Connection sample badge — text box height"
        }
      },
      card: {
        selectors: [".card"],
        text: {
          kind: "length",
          value: "15px",
          role: "Card text — the size the title inherits and the layout and SVG export measure titles at"
        },
        "rule-title-text": {
          kind: "length",
          value: "21px",
          role: "Rule card title on the map"
        },
        "selected-ring-element": {
          kind: "shadow",
          value: "0 0 0 5px color-mix(in srgb,var(--kb-element) 12%,transparent)",
          role: "Selected element card — ring"
        },
        "selected-ring-artifact": {
          kind: "shadow",
          value: "0 0 0 5px color-mix(in srgb,var(--kb-artifact) 12%,transparent)",
          role: "Selected artifact card — ring"
        },
        "selected-ring-frame": {
          kind: "shadow",
          value: "0 0 0 5px color-mix(in srgb,var(--kb-frame) 12%,transparent)",
          role: "Selected frame, factor, option or rule card — ring"
        },
        "selected-background-element": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-element) 15%,var(--kb-surface))",
          role: "Selected element card — background"
        },
        "selected-background-frame": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-frame) 15%,var(--kb-surface))",
          role: "Selected frame, factor, option or rule card — background"
        },
        "border-artifact": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-artifact) 45%,var(--kb-border))",
          role: "Artifact card — border"
        },
        "background-artifact": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-artifact) 5%,var(--kb-surface))",
          role: "Artifact card — background"
        },
        "selected-background-artifact": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-artifact) 15%,var(--kb-surface))",
          role: "Selected artifact card — background"
        },
        "rule-padding-x": {
          kind: "length",
          value: "24px",
          role: "Rule card — horizontal padding"
        },
        "selected-background-option": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-frame) 12%,var(--kb-surface))",
          role: "Selected option card — background"
        },
        "dimmed-border": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-border) 30%,var(--kb-canvas))",
          role: "Dimmed card — border"
        },
        "preview-glow-element": {
          kind: "shadow",
          value: "0 0 7px color-mix(in srgb,var(--kb-element) 13%,transparent)",
          role: "Previewed element card — glow"
        },
        "preview-glow-artifact": {
          kind: "shadow",
          value: "0 0 7px color-mix(in srgb,var(--kb-artifact) 13%,transparent)",
          role: "Previewed artifact card — glow"
        },
        "preview-glow-frame": {
          kind: "shadow",
          value: "0 0 7px color-mix(in srgb,var(--kb-frame) 13%,transparent)",
          role: "Previewed frame, factor, option or rule card — glow"
        },
        "element-indent": {
          kind: "length",
          value: "40px",
          role: "Element card — left padding that clears the kind icon in its corner"
        },
        "hover-filter": {
          kind: "filter",
          value: "brightness(1.04)",
          role: "Card hover luminance"
        },
        "frames-overflow-height": {
          kind: "length",
          value: "17px",
          role: "Card frame overflow pill — text box height"
        },
        "frames-height": {
          kind: "length",
          value: "18px",
          role: "Card frame icon row — height"
        }
      },
      identity: {
        selectors: [".identity"],
        "title-text": {
          kind: "length",
          value: "16px",
          role: "Universe title in the top bar"
        },
        "narrow-clearance": {
          kind: "length",
          value: "78px",
          role: "Top bar identity — right padding keeping the universe title clear of the utility buttons once the bar wraps"
        }
      },
      panel: {
        selectors: [".panel"],
        "head-text": {
          kind: "length",
          value: "18px",
          role: "Detail, search and minimap panel heading"
        },
        "height-max": {
          kind: "length",
          value: "480px",
          role: "Upper bound for floating detail surfaces"
        },
        "box-shadow": {
          kind: "shadow",
          value: "0 12px 32px var(--kb-shadow-medium)",
          role: "Floating panel — lift"
        },
        "height-fraction": {
          kind: "number",
          value: "0.64",
          role: "Maximum detail height relative to viewport"
        },
        "height-narrow-fraction": {
          kind: "number",
          value: "0.4",
          role: "Narrow detail height relative to viewport"
        },
        "height-narrow-max": {
          kind: "length",
          value: "260px",
          role: "Narrow detail height ceiling"
        }
      },
      boundary: {
        selectors: [".boundary"],
        "title-text": {
          kind: "length",
          value: "22px",
          role: "Frame boundary heading on the map and in the SVG export"
        },
        "caption-top": {
          kind: "length",
          value: "28px",
          role: "Boundary caption — drop below the boundary edge, on the map and in the SVG export"
        },
        "scope-border": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-frame) 45%,var(--kb-border))",
          role: "Scope boundary — border"
        }
      },
      chip: {
        selectors: [".chip"],
        "pressed-box-shadow": {
          kind: "shadow",
          value: "inset 0 0 0 1px var(--kb-element)",
          role: "Pressed display chip — inner ring"
        },
        "pressed-background": {
          kind: "color",
          value: "color-mix(in srgb,var(--kb-element) 12%,var(--kb-surface))",
          role: "Pressed display chip — background"
        },
        "box-shadow": {
          kind: "shadow",
          value: "inset 0 0 0 1px var(--kb-border)",
          role: "Display chip — inner ring"
        }
      },
      minimap: {
        selectors: [".minimap"],
        bottom: {
          kind: "length",
          value: "85px",
          role: "Minimap — height above the viewport floor that clears the dock"
        },
        "narrow-bottom": {
          kind: "length",
          value: "150px",
          role: "Minimap — height above the viewport floor once the dock wraps in the narrow layout"
        },
        clearance: {
          kind: "length",
          value: "8px",
          role: "Minimum draggable minimap edge clearance"
        },
        "narrow-width": {
          kind: "length",
          value: "166px",
          role: "Minimap — width in the narrow layout"
        }
      },
      "share-menu": {
        selectors: [".share-menu"],
        "box-shadow": {
          kind: "shadow",
          value: "0 12px 35px var(--kb-shadow-strong)",
          role: "Share menu — lift"
        }
      },
      legend: {
        selectors: [".legend"],
        bottom: {
          kind: "length",
          value: "56px",
          role: "Legend — height above the viewport floor that clears the dock"
        },
        "narrow-bottom": {
          kind: "length",
          value: "117px",
          role: "Legend — height above the viewport floor once the dock wraps in the narrow layout"
        },
        "swatch-width": {
          kind: "length",
          value: "22px",
          role: "Legend key — width of the line swatch"
        }
      },
      scene: {
        selectors: [".world"],
        margin: {
          kind: "length",
          value: "24px",
          role: "Margin the minimap, the fit camera and the SVG export leave around the whole map"
        }
      },
      "view-tabs": {
        selectors: [".view-tabs"],
        "box-shadow": {
          kind: "shadow",
          value: "0 2px 8px var(--kb-shadow-faint)",
          role: "View tab rail — lift"
        },
        "narrow-button-height": {
          kind: "length",
          value: "36px",
          role: "View tab — button height once its label wraps in the narrow layout"
        }
      },
      dock: {
        selectors: [".dock"],
        "box-shadow-2": {
          kind: "shadow",
          value: "0 8px 24px var(--kb-shadow-soft)",
          role: "Dock — lift"
        }
      },
      settings: {
        selectors: [".settings"],
        "box-shadow": {
          kind: "shadow",
          value: "0 12px 40px var(--kb-shadow-medium)",
          role: "Display settings menu — lift"
        },
        width: {
          kind: "length",
          value: "320px",
          role: "Display settings menu — width"
        }
      },
      utility: {
        selectors: [".utilities"],
        "control-size": {
          kind: "length",
          value: "30px",
          role: "Top utility button size"
        }
      },
      viewport: {
        selectors: [".viewport"],
        background: {
          kind: "paint",
          value: "radial-gradient(var(--kb-border) .7px,transparent .7px) 0 0/24px 24px",
          role: "Viewport — dotted board field behind the map"
        }
      },
      detail: {
        selectors: [".detail"],
        width: {
          kind: "length",
          value: "360px",
          role: "Desktop detail width"
        }
      },
      plot: {
        selectors: [".plot"],
        "entity-opacity": {
          kind: "number",
          value: "0.65",
          role: "Minimap entity — opacity"
        },
        height: {
          kind: "length",
          value: "116px",
          role: "Minimap plot — height"
        },
        "camera-stroke": {
          kind: "length",
          value: "1.5px",
          role: "Minimap camera outline — stroke"
        },
        "camera-fill-opacity": {
          kind: "number",
          value: "0.14",
          role: "Minimap camera outline — fill opacity"
        }
      },
      "zoom-readout": {
        selectors: [".zoom-readout"],
        width: {
          kind: "length",
          value: "34px",
          role: "Zoom readout — width that holds the percentage without shifting the dock"
        }
      },
      disclosure: {
        selectors: [".disclosure"],
        "value-width": {
          kind: "length",
          value: "160px",
          role: "Disclosure row — width cap on the value shown at the right"
        }
      },
      overview: {
        selectors: [".overview"],
        width: {
          kind: "length",
          value: "440px",
          role: "Universe overview — width"
        }
      },
      topbar: {
        selectors: [".topbar"],
        "narrow-height": {
          kind: "length",
          value: "132px",
          role: "Top bar — height once it wraps in the narrow layout"
        },
        "compact-identity-column": {
          kind: "length",
          value: "230px",
          role: "Top bar — identity column minimum in the compact layout"
        },
        "utilities-column": {
          kind: "length",
          value: "85px",
          role: "Top bar — utilities column minimum"
        }
      },
      facts: {
        selectors: [".facts"],
        "term-column": {
          kind: "length",
          value: "95px",
          role: "Fact list — width of the term column"
        }
      },
      "active-dot": {
        selectors: [".active-dot"],
        size: {
          kind: "length",
          value: "5px",
          role: "Active dot — diameter of the marker on the universe title"
        }
      },
      divider: {
        selectors: [".divider"],
        thickness: {
          kind: "length",
          value: "1px",
          role: "Divider — rule thickness inside panels"
        }
      },
      label: {
        selectors: [".label", ".leader"],
        closed: true,
        "char-width": {
          kind: "length",
          value: "6.4px",
          role: "Approximate explorer label character advance"
        },
        text: {
          kind: "length",
          value: "var(--kb-type-body-sm)",
          role: "Connection label — text"
        },
        radius: {
          kind: "length",
          value: "var(--kb-radius-xs)",
          role: "Connection label — corner radius"
        },
        border: {
          kind: "length",
          value: "var(--kb-stroke-xs)",
          role: "Connection label — border width"
        },
        leader: {
          kind: "length",
          value: "var(--kb-connection-stroke-leader)",
          role: "Connection label — leader stroke"
        },
        surface: {
          kind: "color",
          value: "var(--kb-canvas)",
          role: "Connection label — fill"
        },
        edge: {
          kind: "color",
          value: "var(--kb-border)",
          role: "Connection label — border colour"
        },
        ink: {
          kind: "color",
          value: "var(--kb-text)",
          role: "Connection label — text colour"
        },
        line: {
          kind: "color",
          value: "var(--kb-element)",
          role: "Connection label — leader colour"
        },
        "zoom-growth": {
          kind: "number",
          value: "var(--kb-zoom-growth-lg)",
          role: "Connection label — zoom growth limit"
        }
      },
      count: {
        selectors: [".count", ".nub-line"],
        closed: true,
        size: {
          kind: "length",
          value: "var(--kb-connection-count-size)",
          role: "Count badge — box"
        },
        gap: {
          kind: "length",
          value: "var(--kb-space-1-5)",
          role: "Count badge — gap to its card"
        },
        text: {
          kind: "length",
          value: "var(--kb-type-body-sm)",
          role: "Count badge — digit"
        },
        radius: {
          kind: "length",
          value: "var(--kb-radius-2xl)",
          role: "Count badge — corner radius"
        },
        border: {
          kind: "length",
          value: "var(--kb-stroke-xs)",
          role: "Count badge — border width"
        },
        stroke: {
          kind: "length",
          value: "var(--kb-connection-stroke-nub)",
          role: "Count badge — leader stroke"
        },
        inset: {
          kind: "length",
          value: "var(--kb-space-1)",
          role: "Count badge — inset offset"
        },
        surface: {
          kind: "color",
          value: "var(--kb-canvas)",
          role: "Count badge — fill"
        },
        edge: {
          kind: "color",
          value: "var(--kb-border)",
          role: "Count badge — border colour"
        },
        ink: {
          kind: "color",
          value: "var(--kb-text)",
          role: "Count badge — digit colour"
        },
        line: {
          kind: "color",
          value: "var(--kb-element)",
          role: "Count badge — leader colour"
        },
        "zoom-growth": {
          kind: "number",
          value: "var(--kb-zoom-growth-sm)",
          role: "Count badge — zoom growth limit"
        },
        layer: {
          kind: "number",
          value: "var(--kb-layer-over-map)",
          role: "Count badge — stacking layer when inset"
        }
      },
      heading: {
        selectors: [".boundary-title", ".boundary-caption"],
        "zoom-growth": {
          kind: "number",
          value: "var(--kb-zoom-growth-sm)",
          role: "Boundary heading — zoom growth limit"
        }
      },
      "card-heading": {
        selectors: [".card-title", ".card-subtitle"],
        "zoom-growth": {
          kind: "number",
          value: "var(--kb-zoom-growth-sm)",
          role: "Card heading — zoom growth limit"
        },
        "description-lines": {
          kind: "number",
          value: "2",
          role: "Frame and factor card description — lines drawn before the text clips"
        },
        "option-description-lines": {
          kind: "number",
          value: "3",
          role: "Option card description — lines drawn before the text clips"
        }
      }
    },
    baseline: {
      source: "knowledge-bus-ui-prototype-tmp/kb-visualizer/visual-tokens.json",
      digest: "sha256:ff654f90adce890365954cc48388cbd3b50a01b0332084cd7b63f2d7feb04905"
    }
  };

  // src/lib/tokens.ts
  var PALETTE = "color";
  var declaresToken = (leaf) => leaf !== null && typeof leaf === "object" && !Array.isArray(leaf);
  function flattenAuthority() {
    const flat = {};
    const groups = visual_tokens_default.roles;
    const parts = visual_tokens_default.parts;
    for (const [group, entries] of Object.entries(groups))
      for (const [leaf, token] of Object.entries(entries))
        if (declaresToken(token)) flat[group === PALETTE ? `--kb-${leaf}` : `--kb-${group}-${leaf}`] = token;
    for (const [part, entries] of Object.entries(parts))
      for (const [leaf, token] of Object.entries(entries)) if (declaresToken(token)) flat[`--kb-${part}-${leaf}`] = token;
    return flat;
  }
  var tokens = flattenAuthority();
  var tokenNames = Object.keys(tokens);
  function tokenValue(name) {
    const token = tokens[name];
    if (!token) throw new Error("Missing visual token " + String(name));
    return token.value;
  }
  var ALIAS = /^var\(\s*(--[\w-]+)\s*\)$/;
  var NESTED_ALIAS = /var\((--[\w-]+)(?:\s*,[^)]*)?\)/g;
  var ALIAS_HOPS = 20;
  var THEME_SPLIT = "light-dark(";
  var numbers = /* @__PURE__ */ new Map();
  var flattenWith = (source, value, depth = 0) => depth > ALIAS_HOPS ? value : value.replace(
    NESTED_ALIAS,
    (whole, name) => source[name] === void 0 ? whole : flattenWith(source, source[name], depth + 1)
  );
  var rawValues = Object.fromEntries(Object.entries(tokens).map(([name, token]) => [name, token.value]));
  function themeIndependent(name, value) {
    if (flattenWith(rawValues, value).includes(THEME_SPLIT))
      throw new Error("Theme-dependent visual token " + String(name) + " has no one number to read");
    return value;
  }
  function tokenNumber(name) {
    const cached = numbers.get(name);
    if (cached !== void 0) return cached;
    let resolved = themeIndependent(name, tokenValue(name));
    for (let depth = 0; depth < ALIAS_HOPS; depth += 1) {
      const alias = resolved.match(ALIAS);
      if (!alias) break;
      resolved = themeIndependent(name, tokenValue(alias[1]));
    }
    const value = parseFloat(resolved);
    if (!Number.isFinite(value)) throw new Error("Non-numeric visual token " + String(name));
    numbers.set(name, value);
    return value;
  }
  function resolveTheme(value, theme) {
    const pair = value.match(/^light-dark\(([^,]+),([^)]+)\)$/);
    return pair ? pair[theme === "light" ? 1 : 2].trim() : value;
  }
  function themeValues(theme) {
    const resolved = {};
    for (const [name, token] of Object.entries(tokens)) resolved[name] = resolveTheme(token.value, theme);
    for (const name of Object.keys(resolved)) resolved[name] = flattenWith(resolved, resolved[name]);
    return resolved;
  }
  function exportThemeCss(selector, theme = "auto") {
    const declarations = (t) => Object.entries(themeValues(t)).map(([name, value]) => `${name}:${value}`).join(";");
    const base = `${selector}{${declarations(theme === "light" ? "light" : "dark")}}`;
    if (theme !== "auto") return base;
    return `${base}@media(prefers-color-scheme:light){${selector}{${declarations("light")}}}`;
  }

  // src/lib/camera.ts
  var noInsets = () => ({ left: 0, right: 0, top: 0, bottom: 0 });
  var MIN_ZOOM = 0.15;
  var MAX_ZOOM = 1.8;
  var EDGE_PAD = 32;
  var FIT_PAD_X = 64;
  var FIT_PAD_Y = 100;
  var FIT_OFFSET_Y = 60;
  var SELECTION_PAD = 64;
  var SELECTION_MAX_ZOOM = 1.2;
  var SAFE_MARGIN = 20;
  var clampZoom = (z) => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z));
  function constrainCamera(target, bounds, viewport, insets = noInsets()) {
    const b = {
      x: bounds.x - insets.left / target.z,
      y: bounds.y - insets.top / target.z,
      w: bounds.w + (insets.left + insets.right) / target.z,
      h: bounds.h + (insets.top + insets.bottom) / target.z
    };
    const clamp = (value, start, size, view) => size * target.z <= view - EDGE_PAD * 2 ? (view - size * target.z) / 2 - start * target.z : Math.max(view - EDGE_PAD - (start + size) * target.z, Math.min(EDGE_PAD - start * target.z, value));
    return {
      z: target.z,
      x: clamp(target.x, b.x, b.w, viewport.width),
      y: clamp(target.y, b.y, b.h, viewport.height)
    };
  }
  function zoomAround(camera, z, cx, cy) {
    const next = clampZoom(z);
    return { z: next, x: cx - (cx - camera.x) * (next / camera.z), y: cy - (cy - camera.y) * (next / camera.z) };
  }
  function fitCamera(bounds, viewport) {
    const z = Math.max(MIN_ZOOM, Math.min((viewport.width - FIT_PAD_X) / bounds.w, (viewport.height - FIT_PAD_Y) / bounds.h));
    return {
      z,
      x: (viewport.width - bounds.w * z) / 2 - bounds.x * z,
      y: (viewport.height - FIT_OFFSET_Y - bounds.h * z) / 2 - bounds.y * z
    };
  }
  function fitCameraWithin(bounds, viewport, insets) {
    const safe = fitCamera(bounds, {
      width: viewport.width - insets.left - insets.right,
      height: viewport.height - insets.top - insets.bottom
    });
    return { z: safe.z, x: safe.x + insets.left, y: safe.y + insets.top };
  }
  function frameCamera(bounds, viewport, insets) {
    const safe = {
      x: insets.left + SAFE_MARGIN,
      y: insets.top + SAFE_MARGIN,
      w: viewport.width - insets.left - insets.right - SAFE_MARGIN * 2,
      h: viewport.height - insets.top - insets.bottom - SAFE_MARGIN * 2
    };
    if (safe.w <= 0 || safe.h <= 0) return null;
    const z = Math.min(SELECTION_MAX_ZOOM, safe.w / (bounds.w + SELECTION_PAD), safe.h / (bounds.h + SELECTION_PAD));
    return {
      z,
      x: safe.x + safe.w / 2 - (bounds.x + bounds.w / 2) * z,
      y: safe.y + safe.h / 2 - (bounds.y + bounds.h / 2) * z
    };
  }
  var EASE_EXPONENT = 3;
  var easeOut = (fraction) => 1 - (1 - Math.min(1, Math.max(0, fraction))) ** EASE_EXPONENT;
  function interpolate(from, to, fraction) {
    const eased = easeOut(fraction);
    return {
      x: from.x + (to.x - from.x) * eased,
      y: from.y + (to.y - from.y) * eased,
      z: from.z + (to.z - from.z) * eased
    };
  }
  var motionDuration = () => tokenNumber("--kb-motion-camera");
  var grow = (zoom, limit) => Math.min(tokenNumber("--kb-zoom-step") ** tokenNumber(limit), Math.max(1, 1 / zoom));
  var boundaryScale = (zoom) => grow(zoom, "--kb-heading-zoom-growth");
  var cardHeadingScale = (zoom) => grow(zoom, "--kb-card-heading-zoom-growth");
  var labelScale = (zoom) => grow(zoom, "--kb-label-zoom-growth");

  // src/lib/labels.ts
  var SAMPLE_COUNT = 41;
  var CARD_CLEARANCE = 8;
  var OFFSET_LADDER = 9;
  var OFFSET_FIRST = 1;
  var OFFSET_GROWTH = 1.5;
  var OFFSET_RUNGS = Array.from({ length: OFFSET_LADDER }, (_, step) => step ? OFFSET_FIRST * OFFSET_GROWTH ** (step - 1) : 0);
  var OFFSET_DIRECTIONS = [
    { x: 0, y: -1 },
    { x: 0, y: 1 },
    { x: -1, y: 0 },
    { x: 1, y: 0 }
  ];
  function labelBox(text, centre, zoom) {
    const scale = grow(zoom, "--kb-label-zoom-growth");
    const w = (text.length * tokenNumber("--kb-label-char-width") + tokenNumber("--kb-connection-label-padding")) * scale;
    const h = tokenNumber("--kb-connection-label-height") * scale;
    return { x: centre.x - w / 2, y: centre.y - h / 2, w, h };
  }
  var penetrationDepth = (box, into) => intersects(box, into) ? Math.min(box.x + box.w - into.x, into.x + into.w - box.x, box.y + box.h - into.y, into.y + into.h - box.y) : 0;
  var straddles = (box, rail) => box.y < rail.y && box.y + box.h > rail.y && box.x < rail.x + rail.w && box.x + box.w > rail.x;
  function placeLabels(candidates, obstacles, zoom, crossings = [], rails = []) {
    const occupied = obstacles.map((r) => expand(r, CARD_CLEARANCE));
    const placed = [];
    for (const candidate of [...candidates].sort((a, b) => (a.edge + a.text).localeCompare(b.edge + b.text))) {
      const plate = labelBox(candidate.text, { x: 0, y: 0 }, zoom);
      const step = plate.h;
      const farthest = OFFSET_RUNGS[OFFSET_RUNGS.length - 1] * step;
      const within = expand(union(candidate.samples.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 }))), farthest + plate.w);
      const nearby = occupied.filter((o) => intersects(o, within));
      const nearbyRails = rails.filter((rail) => intersects({ x: rail.x, y: rail.y, w: rail.w, h: 1 }, within));
      const nearbyCrossings = crossings.filter((c) => contains(within, { x: c.x, y: c.y, w: 0, h: 0 }));
      const scored = candidate.samples.flatMap(
        (point) => OFFSET_RUNGS.flatMap(
          (rung) => (rung ? OFFSET_DIRECTIONS : [{ x: 0, y: 0 }]).map((direction) => {
            const centre = { x: point.x + direction.x * rung * step, y: point.y + direction.y * rung * step };
            const shown = labelBox(candidate.text, centre, zoom);
            return {
              point,
              shown,
              rung,
              blocked: nearby.reduce((deepest, o) => Math.max(deepest, penetrationDepth(shown, o)), 0),
              straddle: nearbyRails.filter((rail) => straddles(shown, rail)).length,
              covered: nearbyCrossings.filter((c) => c.x >= shown.x && c.x <= shown.x + shown.w && c.y >= shown.y && c.y <= shown.y + shown.h).length,
              reach: Math.hypot(point.x - candidate.middle.x, point.y - candidate.middle.y)
            };
          })
        )
      );
      const chosen = scored.sort(
        (a, b) => a.blocked - b.blocked || a.straddle - b.straddle || a.covered - b.covered || a.rung - b.rung || a.reach - b.reach
      )[0];
      if (!chosen) continue;
      occupied.push(expand(chosen.shown, CARD_CLEARANCE));
      placed.push({
        edge: candidate.edge,
        text: candidate.text,
        numeric: candidate.numeric,
        anchor: chosen.point,
        box: chosen.shown
      });
    }
    return placed;
  }
  var sampleCount = () => SAMPLE_COUNT;

  // src/lib/nubs.ts
  var NUB_MARGIN = 2;
  var INSET_OFFSET = 4;
  function placeNubs(counts, rects, scopes, heads, zoom) {
    const scale = grow(zoom, "--kb-count-zoom-growth");
    const size = tokenNumber("--kb-count-size") * scale;
    const gap = tokenNumber("--kb-count-gap") * scale;
    const occupied = [];
    const placed = [];
    const overlaps = (a, b) => a.x < b.x + b.w + NUB_MARGIN && a.x + size > b.x - NUB_MARGIN && a.y < b.y + b.h + NUB_MARGIN && a.y + size > b.y - NUB_MARGIN;
    for (const [id, count] of [...counts].sort(([a], [b]) => a.localeCompare(b))) {
      const r = rects.get(id);
      if (!r || !r.w || !r.h) continue;
      const cx = r.x + r.w / 2;
      const cy = r.y + r.h / 2;
      const candidates = [
        { x: r.x + r.w + gap, y: cy - size / 2, sx: r.x + r.w, sy: cy },
        { x: r.x - gap - size, y: cy - size / 2, sx: r.x, sy: cy },
        { x: cx - size / 2, y: r.y + r.h + gap, sx: cx, sy: r.y + r.h },
        { x: cx - size / 2, y: r.y - gap - size, sx: cx, sy: r.y }
      ];
      const scope = scopes.get(id);
      const inside = (p) => !scope || p.x > scope.x && p.y > scope.y && p.x + size < scope.x + scope.w && p.y + size < scope.y + scope.h;
      const spot = candidates.find(
        (p) => [...rects].every(([key, box]) => key === id || !overlaps(p, box)) && occupied.every((box) => !overlaps(p, box)) && heads.every((box) => !overlaps(p, box)) && inside(p)
      );
      const chosen = spot ?? {
        x: r.x + r.w - size - INSET_OFFSET,
        y: r.y + r.h - size - INSET_OFFSET,
        sx: r.x + r.w,
        sy: r.y + r.h - size / 2 - INSET_OFFSET
      };
      occupied.push({ x: chosen.x, y: chosen.y, w: size, h: size });
      placed.push({
        id,
        count,
        box: { x: chosen.x, y: chosen.y, w: size, h: size },
        from: { x: chosen.sx, y: chosen.sy },
        inset: !spot
      });
    }
    return placed;
  }

  // src/lib/phrasing.ts
  function relationPhrasing(edge, kind, subject = edge.from) {
    if (subject !== edge.from && subject !== edge.to) throw new Error("Displayed subject must be an edge endpoint");
    if (!kind?.phrasing) return null;
    const reversed = subject !== edge.from;
    const phrase = kind.phrasing[kind.ordered && reversed ? "reverse" : "forward"];
    if (!phrase) return null;
    return { subject, object: reversed ? edge.from : edge.to, phrase };
  }
  function compositionDetails(entry) {
    const conditional = !!entry.when && Object.keys(entry.when).length > 0;
    const core = entry.strength === "core";
    return {
      requirement: core ? conditional ? "Required when applicable" : "Required" : "When applicable",
      conditionTitle: conditional ? core ? "Required when" : "Available when" : null,
      fallback: conditional && core ? "Otherwise optional, if the element applies." : null
    };
  }
  var GUIDANCE_HEADING = "How to do this well";
  var guidanceCountCopy = (count) => `${count} ${count === 1 ? "note" : "notes"}`;
  var cardinalityCopy = (cardinality) => cardinality === "singleton" ? "One answer" : cardinality?.startsWith("per-") ? "One per " + cardinality.slice(4).replaceAll("-", " ") : cardinality ? "Answers" : "";
  var cardinalityDetail = (cardinality) => cardinality === "singleton" ? "Not divided into separate answers" : cardinality?.startsWith("per-") ? "One per " + cardinality.slice(4).replaceAll("-", " ") : cardinality || "Not specified";
  var roleCopy = (role) => ({
    ordering: "Organizes elements in a declared order",
    applicability: "Determines whether an artifact is needed",
    gating: "Controls which content applies",
    selection: "Selects content for context"
  })[role ?? ""] ?? role ?? "";
  var setByCopy = (setBy) => ({
    universe: "Fixed for this universe",
    instance: "Set for each piece of work",
    scope: "Set for the relevant scope"
  })[setBy ?? ""] ?? "";
  var legalityCopy = (legality) => ({ permitted: "Permitted", "permitted-if-logged": "Permitted only if recorded", forbidden: "Not permitted" })[legality ?? ""] ?? legality;
  var freezeCopy = (freeze) => ({ open: "Open", baselined: "Changes must be recorded as new events, not edits.", superseded: "Superseded" })[freeze ?? ""] ?? freeze;
  var relationKindCopy = (id, kinds) => kinds.find((k) => k.id === id)?.phrasing?.forward || "Related knowledge";
  var friendly = (id, kinds) => kinds.some((k) => k.id === id) ? relationKindCopy(id, kinds) : human(String(id));
  function distinctFromCopy(from, to) {
    const bothArtifacts = from?.kind === "artifact" && to?.kind === "artifact";
    const bothElements = from?.kind === "element" && to?.kind === "element";
    return bothArtifacts ? "enable different actions" : bothElements ? "answer different questions" : "answer different questions or enable different actions";
  }

  // src/lib/composition-grouping.ts
  var holdingOf = (member) => member.mode === "links" ? "links" : "owns";
  function answerOwners(entries) {
    const owners = /* @__PURE__ */ new Map();
    for (const entry of entries) if (holdingOf(entry) === "owns" && !owners.has(entry.to)) owners.set(entry.to, entry.from);
    return owners;
  }
  var conditionSignature = (when) => Object.entries(when ?? {}).map(([frame, value]) => [frame, Array.isArray(value) ? [...value].map(String).sort().join("|") : String(value)]).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([frame, value]) => `${frame}=${value}`).join(";");
  function compositionGroups(members, owners) {
    const groups = /* @__PURE__ */ new Map();
    const order = [];
    for (const member of members) {
      const copy = compositionDetails(member);
      const key = `${copy.requirement} ${conditionSignature(member.when)}`;
      let group = groups.get(key);
      if (!group) {
        group = { predicate: copy.requirement, conditionTitle: copy.conditionTitle, fallback: copy.fallback, when: member.when, rows: [] };
        groups.set(key, group);
        order.push(key);
      }
      const holding = holdingOf(member);
      group.rows.push({
        target: member.target,
        holding,
        destination: holding === "links" ? owners.get(member.answer ?? member.target) ?? null : null,
        predicate: null
      });
    }
    return order.map((key) => groups.get(key));
  }

  // src/lib/scene.ts
  var holdingDrawn = (edge) => edge.paint === "element" && edge.kind === "composition" ? holdingOf(edge) : null;
  var MAX_DISPLAY_COUNT = 9;
  var MIDPOINT = 0.5;
  var straightSampler = (d, count) => {
    const numbers2 = (d.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
    const points = [];
    for (let i = 0; i + 1 < numbers2.length; i += 2) points.push({ x: numbers2[i], y: numbers2[i + 1] });
    const lengths = points.slice(1).map((p, i) => Math.hypot(p.x - points[i].x, p.y - points[i].y));
    const total = lengths.reduce((a, b) => a + b, 0) || 1;
    const at = (fraction) => {
      let remaining = fraction * total;
      for (let i = 0; i < lengths.length; i += 1) {
        if (remaining <= lengths[i] || i === lengths.length - 1) {
          const ratio = lengths[i] ? remaining / lengths[i] : 0;
          return { x: points[i].x + (points[i + 1].x - points[i].x) * ratio, y: points[i].y + (points[i + 1].y - points[i].y) * ratio };
        }
        remaining -= lengths[i];
      }
      return points[points.length - 1] ?? { x: 0, y: 0 };
    };
    return { samples: Array.from({ length: count }, (_, i) => at((i + 1) / (count + 1))), middle: at(MIDPOINT) };
  };
  function pathPoints(d) {
    const numbers2 = (d.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
    const points = [];
    for (let i = 0; i + 1 < numbers2.length; i += 2) points.push({ x: numbers2[i], y: numbers2[i + 1] });
    return points;
  }
  function baseEdges(model, options) {
    if (options.view === "frames") return [];
    if (!options.connections) return [];
    const source = options.connections === "composition" ? compositionEdges(model) : relationEdges(model);
    return [...source, ...options.connections === "relations" ? wiringEdges(model) : []];
  }
  var SITUATIONAL = "situational";
  var onlyRequiredCompositionIsDrawn = (options) => options.connections === "composition" && options.display === "lines" && options.lineStyle === "uniform";
  function visibleEdges(model, options, layout, selection) {
    const present = new Set(layout.cards.map((c) => c.id));
    const source = baseEdges(model, options);
    const asked = (edges) => onlyRequiredCompositionIsDrawn(options) ? edges.filter((edge) => edge.strength !== SITUATIONAL) : edges;
    if (options.view === "elements") {
      const drawable2 = source.filter((edge) => [edge.from, edge.to, ...edge.targetPair ?? []].every((id) => present.has(id)));
      return asked(bundleExpandedPairs(drawable2, bundleFocusCard(selection.entity, "", "", selection.connection)));
    }
    const artifactIds = layout.cards.filter((c) => c.kind === "artifact").map((c) => c.id);
    const rolled = artifactEdges(
      source.filter((edge) => !edge.targetPair),
      compositionEntries(model),
      artifactIds,
      options.connections === "composition" ? "composition" : "relations"
    );
    return asked(collapseCardPairs(rolled.filter((e) => present.has(e.from) && present.has(e.to))));
  }
  function relatedTo(edges, focus) {
    const related = new Set(focus ? [focus] : []);
    for (const edge of edges)
      if (edge.from === focus || edge.to === focus || edge.targetPair?.includes(focus)) {
        related.add(edge.from);
        related.add(edge.to);
        for (const id of edge.targetPair ?? []) related.add(id);
        related.add(edge.path);
      }
    return related;
  }
  var NUB_OWNER = "nub:";
  var nubOwnerCard = (connection) => connection.startsWith(NUB_OWNER) ? connection.slice(NUB_OWNER.length) : "";
  var edgeTouches = (edge, id) => edge.from === id || edge.to === id || edge.targetPair?.includes(id) === true;
  function cardWithKin(edges, id) {
    const kin = /* @__PURE__ */ new Set([id]);
    for (const edge of edges)
      if (edgeTouches(edge, id)) for (const endpoint of [edge.from, edge.to, ...edge.targetPair ?? []]) kin.add(endpoint);
    return kin;
  }
  function nubLayer(layout, edges, zoom) {
    const counts = /* @__PURE__ */ new Map();
    for (const edge of edges)
      for (const id of /* @__PURE__ */ new Set([edge.from, edge.to, ...edge.targetPair ?? []]))
        counts.set(id, (counts.get(id) ?? 0) + (edge.sources?.length ?? 1));
    const boundaryById = new Map(layout.boundaries.map((b) => [b.id, b]));
    const scopes = /* @__PURE__ */ new Map();
    for (const card of layout.cards) {
      const owner = boundaryById.get(card.scopeId);
      if (owner) scopes.set(card.id, owner);
    }
    return placeNubs(counts, cardRects(layout), scopes, boundaryHeads(layout), zoom);
  }
  var boundaryRails = (layout) => layout.boundaries.flatMap((b) => [
    { x: b.x, y: b.y, w: b.w },
    { x: b.x, y: b.y + b.h, w: b.w }
  ]);
  function labelLayer(layout, edges, candidates, zoom) {
    if (!candidates.length) return [];
    return placeLabels(
      candidates,
      [...layout.cards.map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h })), ...boundaryHeads(layout)],
      zoom,
      polylineCrossings(edges.filter((e) => e.drawn).map((e) => e.points)),
      boundaryRails(layout)
    );
  }
  function buildScene(model, options, selection, zoom = 1, sampler = straightSampler) {
    const layout = layoutFor(model, options);
    const rects = cardRects(layout);
    const edges = visibleEdges(model, options, layout, selection);
    const focus = selection.entity;
    const related = relatedTo(edges, focus);
    const router = new Router();
    router.begin();
    const emphasisActive = options.connections === "relations" && options.emphasis.length > 0;
    const countsOnly = options.display === "counts";
    const scened = edges.map((edge) => {
      const a = rects.get(edge.from);
      const b = edge.targetPair ? (() => {
        const p = rects.get(edge.targetPair[0]);
        const q = rects.get(edge.targetPair[1]);
        return { x: (p.x + p.w / 2 + q.x + q.w / 2) / 2, y: (p.y + p.h + q.y) / 2, w: 0, h: 0 };
      })() : rects.get(edge.to);
      const d = edge.targetPair ? `M ${a.x + a.w / 2} ${a.y + a.h} L ${b.x} ${b.y}` : router.path(a, b, rects, { from: edge.from, to: edge.to, kind: edge.kind, strength: edge.strength, label: edge.label });
      const points = pathPoints(d);
      const on = !!focus && (edge.from === focus || edge.to === focus || edge.targetPair?.includes(focus) === true);
      const grade = edge.targetPair || options.lineStyle !== "distinct" || options.connections !== "composition" ? null : edge.strength === "situational" ? "situational" : edge.strength === "mixed" ? "mixed" : "required";
      const dash = edge.targetPair ? "frame" : grade === "situational" || grade === "mixed" ? grade : "none";
      return {
        ...edge,
        drawn: !countsOnly || on || selection.connection === edge.path,
        d,
        points,
        on,
        emphasized: emphasisActive && options.emphasis.includes(edge.kind ?? ""),
        dash,
        grade,
        paint: edge.targetPair ? "frame" : edge.rolled ? "rolled" : "element",
        midpoint: points.length ? points[Math.floor(points.length / 2)] : { x: a.x, y: a.y }
      };
    });
    const cardList = layout.cards.map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h }));
    let labelCandidates = [];
    let nubs = [];
    if (countsOnly && !focus) {
      nubs = nubLayer(layout, scened, zoom);
    } else {
      const shown = scened.filter((edge) => edge.drawn && (edge.on || selection.connection === edge.path));
      labelCandidates = shown.map((edge) => {
        const { samples, middle } = sampler(edge.d, sampleCount());
        const numeric = options.view !== "elements" || !!edge.bundled;
        const count = edge.sources?.length ?? 1;
        return {
          edge: edge.path,
          text: numeric ? count > MAX_DISPLAY_COUNT ? `${MAX_DISPLAY_COUNT}+` : String(count) : edge.label,
          numeric,
          samples,
          middle
        };
      });
    }
    const labels = labelLayer(layout, scened, labelCandidates, zoom);
    return { layout, edges: scened, labelCandidates, labels, nubs, related, focus, zoom, bounds: union([...cardList, ...layout.boundaries]) };
  }
  var LEGEND_ROWS = ["direct", "rolled", "required", "situational", "mixed", "owns", "links"];
  var LEGEND_ROW_HOLDING = { owns: "owns", links: "links" };
  var drawnEdgeEachLegendRowDescribes = {
    direct: (edge) => edge.paint === "element",
    rolled: (edge) => edge.paint === "rolled",
    required: (edge) => edge.grade === "required",
    situational: (edge) => edge.grade === "situational",
    mixed: (edge) => edge.grade === "mixed",
    owns: (edge) => holdingDrawn(edge) === "owns",
    links: (edge) => holdingDrawn(edge) === "links"
  };
  var legendRows = (scene) => LEGEND_ROWS.filter((row) => scene.edges.some((edge) => edge.drawn && drawnEdgeEachLegendRowDescribes[row](edge)));
  function subjectBounds(scene, selection) {
    const subject = selection.entity || nubOwnerCard(selection.connection) || selection.option;
    if (subject) {
      const card = scene.layout.cards.find((c) => c.id === subject);
      if (card) return { x: card.x, y: card.y, w: card.w, h: card.h };
      const boundary = scene.layout.boundaries.find((b) => b.id === subject);
      if (boundary) return boundary;
    }
    if (selection.connection) {
      const edge = scene.edges.find((e) => e.path === selection.connection);
      if (edge?.points.length) return union(edge.points.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 })));
    }
    return null;
  }
  function selectionBounds(scene, selection) {
    const ids = /* @__PURE__ */ new Set();
    const nubOwner = nubOwnerCard(selection.connection);
    if (nubOwner) for (const id of cardWithKin(scene.edges, nubOwner)) ids.add(id);
    else if (selection.connection) {
      const edge = scene.edges.find((e) => e.path === selection.connection);
      if (edge) {
        ids.add(edge.from);
        ids.add(edge.to);
        for (const id of edge.targetPair ?? []) ids.add(id);
      }
    } else if (selection.entity) for (const id of scene.related) ids.add(id);
    else if (selection.option) ids.add(selection.option);
    const boxes = scene.layout.cards.filter((c) => ids.has(c.id)).map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h }));
    for (const boundary of scene.layout.boundaries) if (ids.has(boundary.id)) boxes.push(boundary);
    for (const edge of scene.edges)
      if (selection.connection && edge.path === selection.connection || selection.entity && edge.on)
        boxes.push(union(edge.points.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 }))));
    return boxes.length ? union(boxes) : null;
  }

  // src/lib/icons.ts
  var ICON_GRID = 24;
  var MONOGRAM_TYPE_SIZE = 13;
  var paths = {
    close: "M6 6l12 12M18 6 6 18",
    menu: "M4 6h16M4 12h16M4 18h16",
    search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6",
    share: "M12 16V3m-5 5 5-5 5 5M4 14v7h16v-7",
    copy: "M9 9h11v11H9ZM5 15H4V4h11v1",
    image: "M3 4h18v16H3ZM3 16l5-5 4 4 3-3 6 6",
    vector: "M4 4h4v4H4ZM16 16h4v4h-4ZM8 6h8M18 8v8",
    map: "M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16",
    fit: "M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6",
    plus: "M12 5v14M5 12h14",
    minus: "M5 12h14",
    actual: "M4 4h16v16H4ZM9 9h6v6H9",
    back: "M11 5l-7 7 7 7M4 12h16",
    forward: "M13 5l7 7-7 7M20 12H4",
    chevron: "M9 5l7 7-7 7",
    "chevron-down": "m6 9 6 6 6-6",
    filter: "M3 5h18l-7 8v6l-4-2v-4Z",
    options: "M4 6h16M4 12h16M4 18h16M9 4v4M15 10v4M7 16v4",
    reset: "M3 3v6h6M4 9a9 9 0 1 1-1 6",
    clear: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M5 5l14 14",
    check: "M4 12l5 5L20 6",
    network: "M9 3h6v6H9ZM2 15h6v6H2ZM16 15h6v6h-6M12 9v3M5 15v-3h14v3",
    artifacts: "M4 4h16v16H4Z",
    combined: "M3 4h18v4H3ZM3 10h8v10H3ZM13 10h8v10h-8Z",
    sun: "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10M12 1v3M12 20v3M1 12h3M20 12h3M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2",
    moon: "M20 14a8 8 0 1 1-10-10 7 7 0 0 0 10 10Z",
    frame: "M4 4h16v16H4ZM8 8h8v8H8",
    factor: "M12 3l9 6-9 6-9-6ZM3 15l9 6 9-6",
    artifact: "M5 2h10l4 4v16H5ZM14 2v5h5M8 12h8M8 16h8",
    element: "M12 2 22 12 12 22 2 12Z",
    rule: "M4 4h16v16H4ZM8 12h8"
  };
  var wordsOf = (label) => label.split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  function monogramsAvailableTo(label) {
    const words = wordsOf(label);
    const first = words[0] ?? "";
    if (!first) return [];
    const head = first[0].toUpperCase();
    const available = words.slice(1).map((word) => head + word[0].toUpperCase());
    for (let index = 1; index < first.length; index += 1) available.push(head + first[index].toLowerCase());
    if (!available.length) available.push(head);
    for (let ordinal = 2; ordinal <= 9; ordinal += 1) available.push(head + String(ordinal));
    return available;
  }
  var markableConcepts = (model) => {
    const drawnBeforeItsPeers = (entity) => entity.kind === "frame" || entity.kind === "factor" ? 0 : entity.frameId === model.orderingFrameId ? 1 : 2;
    return model.entities.filter((entity) => entity.kind === "frame" || entity.kind === "factor" || entity.kind === "option").sort((a, b) => drawnBeforeItsPeers(a) - drawnBeforeItsPeers(b) || a.label.localeCompare(b.label));
  };
  var marksBuiltForModel = /* @__PURE__ */ new WeakMap();
  function marksOf(model) {
    const already = marksBuiltForModel.get(model);
    if (already) return already;
    const universeDeclared = model.marks?.declared ?? {};
    const taken = /* @__PURE__ */ new Set();
    for (const mark of Object.values(universeDeclared)) if ("monogram" in mark) taken.add(mark.monogram);
    const monogramOfLabel = /* @__PURE__ */ new Map();
    const frameConcepts = /* @__PURE__ */ new Map();
    const valueConcepts = /* @__PURE__ */ new Map();
    for (const concept of markableConcepts(model)) {
      if (concept.kind === "option") valueConcepts.set(`${concept.frameId ?? ""} ${concept.sourceId}`, concept);
      else frameConcepts.set(concept.sourceId, concept);
      if (universeDeclared[concept.id] || monogramOfLabel.has(concept.label)) continue;
      const chosen = monogramsAvailableTo(concept.label).find((candidate) => !taken.has(candidate));
      if (!chosen) continue;
      taken.add(chosen);
      monogramOfLabel.set(concept.label, chosen);
    }
    const markOf = (concept, label, fallback) => {
      const declared = concept && universeDeclared[concept.id];
      if (declared) return declared;
      const assigned = monogramOfLabel.get(label) ?? monogramsAvailableTo(label)[0];
      return assigned ? { monogram: assigned } : { glyph: paths[fallback] ?? paths.frame };
    };
    const marks = {
      frame: (sourceId, fallback = "frame") => {
        const concept = frameConcepts.get(sourceId);
        return markOf(concept, concept?.label ?? human(sourceId), fallback);
      },
      value: (frameId, value, fallback = "frame") => {
        const concept = valueConcepts.get(`${frameId} ${value}`);
        return markOf(concept, concept?.label ?? human(value), fallback);
      }
    };
    marksBuiltForModel.set(model, marks);
    return marks;
  }

  // src/lib/card.ts
  var AVERAGE_GLYPH_RATIO = 0.55;
  var approximateText = (text, size) => text.length * size * AVERAGE_GLYPH_RATIO;
  var MAX_FRAME_ICONS = 3;
  function wrap(text, width, size, measure = approximateText) {
    const lines = [];
    let line = "";
    for (const word of text.split(/\s+/).filter(Boolean)) {
      if (line && measure(line + " " + word, size) > width) {
        lines.push(line);
        line = word;
      } else line += (line ? " " : "") + word;
    }
    if (line) lines.push(line);
    return lines;
  }
  function subtitleFor(card, entity, model) {
    if (card.kind === "rule") return "No artifact contents are required in this context.";
    if (!entity) return "";
    if (entity.kind === "element") return cardinalityCopy(entity.raw.cardinality);
    if (entity.kind === "frame" || entity.kind === "factor") return entity.description || setByCopy(entity.raw.set_by);
    if (entity.kind === "option") return entity.description;
    return "";
  }
  function matchFor(card, model) {
    if (card.kind !== "frame") return "";
    const rule = model.rules[0];
    const values = (rule?.raw.when ?? {})[card.entity?.sourceId ?? ""];
    return values ? values.map(human).join(" or ") : "";
  }
  function cardAnatomy(card, model, measure = approximateText) {
    const entity = card.entity;
    const accent = card.kind === "artifact" ? "--kb-artifact" : card.kind === "element" ? "--kb-element" : card.kind === "rule" ? "--kb-border" : "--kb-frame";
    const ordering = model.orderingFrameId.split(":").slice(1).join(":");
    const marks = marksOf(model);
    const icon2 = card.kind === "element" ? marks.value(model.orderingFrameId, String(entity?.frameValues[ordering] ?? entity?.raw[ordering] ?? ""), "element") : card.kind === "option" ? marks.value(entity?.frameId ?? "", entity?.sourceId ?? "", "frame") : card.kind === "frame" || card.kind === "factor" ? marks.frame(entity?.sourceId ?? "", card.kind) : null;
    const title = card.kind === "rule" ? "No artifact needed" : entity?.label ?? human(card.id.split(":").pop() ?? "");
    const subtitle = subtitleFor(card, entity, model);
    const frameNames = entity && (entity.kind === "element" || entity.kind === "artifact") ? referencedFrames(model, entity.id).filter((frame) => frame !== ordering) : [];
    const padding = tokenNumber("--kb-space-3");
    const iconSize = tokenNumber("--kb-icon-base");
    const textWidth = card.w - padding * 2 - (icon2 ? iconSize + tokenNumber("--kb-space-2") : 0);
    return {
      accent,
      edge: card.kind === "artifact" || card.kind === "frame" || card.kind === "factor" ? "top" : "left",
      icon: icon2,
      title,
      titleLines: wrap(title, textWidth, tokenNumber("--kb-card-text"), measure),
      subtitle,
      subtitleLines: wrap(subtitle, textWidth, tokenNumber("--kb-type-body-sm"), measure),
      frameIcons: frameNames.slice(0, MAX_FRAME_ICONS).map((frame) => marks.frame(frame)),
      frameNames: frameNames.map(human),
      overflow: frameNames.length > MAX_FRAME_ICONS ? `+${frameNames.length - MAX_FRAME_ICONS}` : "",
      match: matchFor(card, model)
    };
  }

  // src/lib/export.ts
  var escapeXml = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[c]);
  var COORDINATE_PRECISION = 100;
  var round = (n) => String(Math.round(n * COORDINATE_PRECISION) / COORDINATE_PRECISION);
  var MAX_DISPLAY_COUNT2 = 9;
  var DASH = { none: "", situational: "--kb-connection-dash-situational", mixed: "", frame: "--kb-connection-dash-frame" };
  var MIXED_DASH = "12 3 3 3";
  function serializeSvg(scene, model, theme = "auto", measure = approximateText) {
    const pad = tokenNumber("--kb-scene-margin");
    const b = scene.bounds;
    const width = b.w + pad * 2;
    const height = b.h + pad * 2;
    const paint = (name) => `var(${name})`;
    const out = [];
    const text = (x, y, value, size, fill, weight, anchor) => `<text x="${round(x)}" y="${round(y)}" font-size="${round(size)}" fill="${fill}"${weight ? ` font-weight="${weight}"` : ""}${anchor ? ` text-anchor="${anchor}"` : ""}>${escapeXml(value)}</text>`;
    const drawn = (x, y, data2, size, stroke) => `<path d="${escapeXml(data2)}" transform="translate(${round(x)} ${round(y)}) scale(${round(size / ICON_GRID)})" fill="none" stroke="${stroke}" stroke-width="${round(ICON_GRID / size * tokenNumber("--kb-stroke-sm"))}" stroke-linecap="round" stroke-linejoin="round"/>`;
    const drawnMark = (x, y, mark, size, ink) => "monogram" in mark ? `<text x="${round(x + size / 2)}" y="${round(y + size / 2)}" font-size="${round(size * MONOGRAM_TYPE_SIZE / ICON_GRID)}" fill="${ink}" text-anchor="middle" dominant-baseline="central">${escapeXml(mark.monogram)}</text>` : drawn(x, y, mark.glyph, size, ink);
    out.push(
      `<rect x="${round(b.x - pad)}" y="${round(b.y - pad)}" width="${round(width)}" height="${round(height)}" fill="${paint("--kb-canvas")}"/>`
    );
    const headingSize = tokenNumber("--kb-boundary-title-text");
    const captionSize = tokenNumber("--kb-type-body");
    const lineGap = tokenNumber("--kb-space-4");
    for (const boundary of scene.layout.boundaries) {
      const stroke = boundary.role === "scope" ? paint("--kb-boundary-scope-border") : paint("--kb-border");
      out.push(
        `<rect x="${round(boundary.x)}" y="${round(boundary.y)}" width="${round(boundary.w)}" height="${round(boundary.h)}" rx="${round(tokenNumber("--kb-radius-4xl"))}" fill="none" stroke="${stroke}"/>`
      );
      if (boundary.title)
        out.push(
          text(
            boundary.x + tokenNumber("--kb-space-5"),
            boundary.y + tokenNumber("--kb-space-1-5"),
            boundary.title,
            headingSize,
            boundary.role === "scope" ? paint("--kb-frame") : paint("--kb-text"),
            tokenNumber("--kb-weight-medium")
          )
        );
      if (boundary.caption)
        out.push(
          text(
            boundary.x + tokenNumber("--kb-space-5"),
            boundary.y + tokenNumber("--kb-boundary-caption-top") + lineGap,
            boundary.caption,
            captionSize,
            paint("--kb-text-muted")
          )
        );
    }
    for (const note of scene.layout.notes)
      out.push(text(note.x + note.w / 2, note.y + note.h / 2, note.text, captionSize, paint("--kb-text-muted"), void 0, "middle"));
    const strokeBase = tokenNumber("--kb-connection-stroke-base");
    for (const edge of scene.edges) {
      if (!edge.drawn) continue;
      const stroke = edge.paint === "rolled" ? paint("--kb-connection-rolled") : edge.paint === "frame" ? paint("--kb-frame") : paint("--kb-element");
      const dashToken = DASH[edge.dash];
      const dash = edge.dash === "mixed" ? MIXED_DASH : dashToken ? `var(${dashToken})` : "";
      out.push(
        `<path d="${edge.d}" fill="none" stroke="${stroke}" stroke-width="${round(strokeBase)}"${dash ? ` stroke-dasharray="${dash}"` : ""} opacity="${round(tokenNumber("--kb-connection-opacity-normal"))}"/>`
      );
      if (edge.ordered && edge.points.length > 1) {
        const end = edge.points[edge.points.length - 1];
        const before = edge.points[edge.points.length - 2];
        const dx = Math.sign(end.x - before.x);
        const dy = Math.sign(end.y - before.y) || (dx ? 0 : 1);
        const size = tokenNumber("--kb-space-2");
        const tip = dy ? [end, { x: end.x - size / 2, y: end.y - dy * size }, { x: end.x + size / 2, y: end.y - dy * size }] : [end, { x: end.x - dx * size, y: end.y - size / 2 }, { x: end.x - dx * size, y: end.y + size / 2 }];
        out.push(`<polygon points="${tip.map((p) => `${round(p.x)},${round(p.y)}`).join(" ")}" fill="${stroke}"/>`);
      }
    }
    const labelHeight = tokenNumber("--kb-connection-label-height");
    const named = byId(model);
    const nameOf = (id) => named.get(id)?.label ?? human(id.split(":").pop() ?? id);
    const endsOfEachEdge = /* @__PURE__ */ new Map();
    for (const edge of scene.edges)
      endsOfEachEdge.set(
        edge.path,
        edge.targetPair ? `${nameOf(edge.from)} · ${nameOf(edge.targetPair[0])} and ${nameOf(edge.targetPair[1])}` : `${nameOf(edge.from)} · ${nameOf(edge.to)}`
      );
    for (const label of scene.labels) {
      out.push(`<g><title>${escapeXml(endsOfEachEdge.get(label.edge) ?? "")}</title>`);
      out.push(
        `<rect x="${round(label.box.x)}" y="${round(label.box.y)}" width="${round(label.box.w)}" height="${round(label.box.h)}" rx="${round(tokenNumber("--kb-radius-xs"))}" fill="${paint("--kb-canvas")}"/>`
      );
      out.push(
        text(
          label.box.x + label.box.w / 2,
          label.box.y + labelHeight / 2 + tokenNumber("--kb-connection-label-baseline-offset"),
          label.text,
          tokenNumber("--kb-type-body-sm"),
          paint("--kb-text"),
          void 0,
          "middle"
        )
      );
      out.push("</g>");
    }
    for (const nub of scene.nubs) {
      if (!nub.inset)
        out.push(
          `<path d="M ${round(nub.from.x)} ${round(nub.from.y)} L ${round(nub.box.x + nub.box.w / 2)} ${round(nub.box.y + nub.box.h / 2)}" stroke="${paint("--kb-element")}" stroke-width="${round(tokenNumber("--kb-connection-stroke-nub"))}" fill="none"/>`
        );
      out.push(
        `<rect x="${round(nub.box.x)}" y="${round(nub.box.y)}" width="${round(nub.box.w)}" height="${round(nub.box.h)}" rx="${round(tokenNumber("--kb-radius-2xl"))}" fill="${paint("--kb-canvas")}" stroke="${paint("--kb-border")}"/>`
      );
      out.push(
        text(
          nub.box.x + nub.box.w / 2,
          nub.box.y + nub.box.h / 2 + tokenNumber("--kb-connection-label-baseline-offset"),
          nub.count > MAX_DISPLAY_COUNT2 ? `${MAX_DISPLAY_COUNT2}+` : String(nub.count),
          tokenNumber("--kb-type-body-sm"),
          paint("--kb-text"),
          void 0,
          "middle"
        )
      );
    }
    for (const card of scene.layout.cards) {
      const anatomy = cardAnatomy(card, model, measure);
      const accent = paint(anatomy.accent);
      out.push(`<g data-entity="${escapeXml(card.id)}">`);
      out.push(
        `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(card.w)}" height="${round(card.h)}" rx="${round(tokenNumber("--kb-radius-md"))}" fill="${paint("--kb-surface")}" stroke="${paint("--kb-border")}"/>`
      );
      if (anatomy.edge === "top")
        out.push(
          `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(card.w)}" height="${round(tokenNumber("--kb-stroke-lg"))}" fill="${accent}"/>`
        );
      else
        out.push(
          `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(tokenNumber("--kb-stroke-lg"))}" height="${round(card.h)}" fill="${accent}"/>`
        );
      const padding = tokenNumber("--kb-space-3");
      const iconSize = tokenNumber("--kb-icon-base");
      let cursor = card.y + padding + tokenNumber("--kb-card-text");
      if (anatomy.icon) {
        out.push(drawnMark(card.x + padding, card.y + padding, anatomy.icon, iconSize, accent));
      }
      const textX = card.x + padding + (anatomy.icon ? iconSize + tokenNumber("--kb-space-2") : 0);
      for (const line of anatomy.titleLines) {
        out.push(text(textX, cursor, line, tokenNumber("--kb-card-text"), paint("--kb-text"), tokenNumber("--kb-weight-medium")));
        cursor += tokenNumber("--kb-space-4");
      }
      for (const line of anatomy.subtitleLines) {
        out.push(text(textX, cursor, line, tokenNumber("--kb-type-body-sm"), paint("--kb-text-muted")));
        cursor += tokenNumber("--kb-space-4");
      }
      if (anatomy.match)
        out.push(
          text(
            card.x + padding,
            card.y + card.h - padding,
            anatomy.match,
            tokenNumber("--kb-type-body-lg"),
            paint("--kb-text"),
            tokenNumber("--kb-weight-medium")
          )
        );
      anatomy.frameIcons.forEach(
        (name, index) => out.push(
          drawnMark(
            card.x + padding + index * (iconSize + tokenNumber("--kb-space-2")),
            card.y + card.h - padding - iconSize,
            name,
            iconSize,
            paint("--kb-frame")
          )
        )
      );
      if (anatomy.overflow)
        out.push(
          text(
            card.x + padding + anatomy.frameIcons.length * (iconSize + tokenNumber("--kb-space-2")),
            card.y + card.h - padding,
            anatomy.overflow,
            tokenNumber("--kb-type-caption"),
            paint("--kb-text-muted")
          )
        );
      out.push("</g>");
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="display:block;width:100vw;height:100vh" viewBox="${round(b.x - pad)} ${round(b.y - pad)} ${round(width)} ${round(height)}" preserveAspectRatio="xMidYMid meet" role="img"><title>${escapeXml(model.universe.label)}</title><desc>${escapeXml(`Knowledge Bus universe map: ${human(model.universe.id)}. Current presentation options; no transient selection.`)}</desc><style>${exportThemeCss("svg", theme)}text{font-family:var(--kb-font-sans)}</style>` + out.join("") + "</svg>";
  }

  // src/lib/dwell.ts
  var wallClock = {
    setTimeout: (run, delay) => globalThis.setTimeout(run, delay),
    clearTimeout: (pending) => globalThis.clearTimeout(pending)
  };
  function showAfterTheLastOfferRests(first, rest, show, clock = wallClock) {
    let shown = first;
    let pending = null;
    const forget = () => {
      if (pending !== null) clock.clearTimeout(pending);
      pending = null;
    };
    return {
      shown: () => shown,
      offer(value) {
        forget();
        if (value === shown) return;
        pending = clock.setTimeout(() => {
          pending = null;
          shown = value;
          show(value);
        }, rest);
      },
      showNow(value) {
        forget();
        shown = value;
      }
    };
  }

  // src/component-elements/card-surface.ts
  function cardSurface(id, kind, box, label, action) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "card";
    card.dataset.id = id;
    card.dataset.kind = kind;
    card.dataset.state = "idle";
    card.dataset.preview = "false";
    card.setAttribute("aria-label", label);
    card.setAttribute("aria-pressed", "false");
    card.style.left = `${box.x}px`;
    card.style.top = `${box.y}px`;
    card.style.width = `${box.w}px`;
    card.style.height = `${box.h}px`;
    card.addEventListener("click", (event) => {
      event.stopPropagation();
      action(event);
    });
    return card;
  }
  function setCardState(card, state, preview = false) {
    card.dataset.state = state;
    card.dataset.preview = String(preview);
    card.setAttribute("aria-pressed", String(state === "selected"));
  }

  // src/component-elements/icon.ts
  var SVG = "http://www.w3.org/2000/svg";
  function iconFrame(label) {
    const svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("viewBox", `0 0 ${ICON_GRID} ${ICON_GRID}`);
    svg.setAttribute("class", "icon");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    if (label) {
      svg.setAttribute("role", "img");
      const title = document.createElementNS(SVG, "title");
      title.textContent = label;
      svg.append(title);
    } else svg.setAttribute("aria-hidden", "true");
    return svg;
  }
  function drawnPath(data2) {
    const path = document.createElementNS(SVG, "path");
    path.setAttribute("d", data2);
    return path;
  }
  function drawnMonogram(letters) {
    const text = document.createElementNS(SVG, "text");
    text.setAttribute("x", String(ICON_GRID / 2));
    text.setAttribute("y", String(ICON_GRID / 2));
    text.setAttribute("font-size", String(MONOGRAM_TYPE_SIZE));
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "central");
    text.setAttribute("fill", "currentColor");
    text.setAttribute("stroke", "none");
    text.textContent = letters;
    return text;
  }
  function icon(name, label) {
    const svg = iconFrame(label);
    svg.append(drawnPath(paths[name] ?? paths.frame));
    return svg;
  }
  function markIcon(mark, label) {
    const svg = iconFrame(label);
    svg.append("monogram" in mark ? drawnMonogram(mark.monogram) : drawnPath(mark.glyph));
    return svg;
  }

  // src/component-patterns/entity-card.ts
  function entityCard(card, model, select, measure) {
    const anatomy = cardAnatomy(card, model, measure);
    const surface = cardSurface(card.id, card.kind, card, anatomy.title, () => select(card.id));
    if (card.kind === "element" && anatomy.icon) {
      const badge = document.createElement("span");
      badge.className = "card-order-icon";
      badge.setAttribute("aria-label", anatomy.subtitle ? `${anatomy.title}, ${anatomy.subtitle}` : anatomy.title);
      badge.append(markIcon(anatomy.icon));
      surface.append(badge);
    }
    const title = document.createElement("strong");
    title.className = "card-title";
    title.dataset.part = "card-heading";
    if (anatomy.icon && card.kind !== "element") title.append(markIcon(anatomy.icon));
    const titleText = document.createElement("span");
    titleText.textContent = anatomy.title;
    title.append(titleText);
    surface.append(title);
    if (anatomy.subtitle) {
      const subtitle = document.createElement("span");
      subtitle.className = "card-subtitle";
      subtitle.dataset.part = "card-heading";
      subtitle.textContent = anatomy.subtitle;
      surface.append(subtitle);
    }
    if (anatomy.match) {
      const match = document.createElement("span");
      match.className = "card-match";
      match.textContent = anatomy.match;
      surface.append(match);
    }
    if (anatomy.frameIcons.length) {
      const row = document.createElement("span");
      row.className = "card-frames";
      row.setAttribute("aria-label", `Referenced frames: ${anatomy.frameNames.join(", ")}`);
      anatomy.frameIcons.forEach((name, index) => {
        const slot = document.createElement("span");
        slot.title = anatomy.frameNames[index];
        slot.append(markIcon(name, anatomy.frameNames[index]));
        row.append(slot);
      });
      if (anatomy.overflow) {
        const overflow = document.createElement("span");
        overflow.className = "card-frames-overflow";
        overflow.textContent = anatomy.overflow;
        overflow.setAttribute("aria-label", anatomy.frameNames.slice(anatomy.frameIcons.length).join(", "));
        row.append(overflow);
      }
      surface.append(row);
      surface.title = anatomy.frameNames.join(" · ");
    }
    return surface;
  }
  function optionCard(card, model, stats, select) {
    const anatomy = cardAnatomy(card, model);
    const surface = cardSurface(card.id, "option", card, anatomy.title, () => select(card.id));
    if (anatomy.icon) surface.append(markIcon(anatomy.icon));
    const title = document.createElement("strong");
    title.className = "card-title";
    title.dataset.part = "card-heading";
    title.textContent = anatomy.title;
    surface.append(title);
    if (anatomy.subtitle) {
      const question = document.createElement("span");
      question.className = "card-subtitle";
      question.dataset.part = "card-heading";
      question.textContent = anatomy.subtitle;
      surface.append(question);
    }
    const counts = document.createElement("span");
    counts.className = "card-stats";
    counts.textContent = `${stats.artifacts} Artifacts  ${stats.elements} Elements`;
    surface.append(counts);
    return surface;
  }

  // src/lib/emphasis.ts
  function emphasise(scene, selection, hover) {
    const cards = /* @__PURE__ */ new Map();
    const edges = /* @__PURE__ */ new Map();
    const nubs = /* @__PURE__ */ new Map();
    const edgeIds = new Set(scene.edges.map((e) => e.path));
    const ownedByNub = nubOwnerCard(selection.connection);
    const selectedCard = selection.entity || selection.option || ownedByNub;
    const hoveredEdge = edgeIds.has(hover) ? hover : "";
    const hoveredCard = hoveredEdge ? "" : hover;
    const subjectEdge = (ownedByNub ? "" : selection.connection) || (selectedCard ? "" : hoveredEdge);
    const subjectCard = selectedCard || (subjectEdge ? "" : hoveredCard);
    const settled = !!selectedCard || !!selection.connection;
    const preview = hoveredCard && hoveredCard !== selectedCard && !subjectEdge ? hoveredCard : "";
    const quietest = settled ? "dimmed" : "hushed";
    const faintest = settled ? "hidden" : "rest";
    const hoveredInsideSubjectSet = !subjectEdge && subjectCard && scene.edges.some((e) => e.path === hoveredEdge && edgeTouches(e, subjectCard)) ? hoveredEdge : "";
    const kin = /* @__PURE__ */ new Set();
    if (subjectEdge) {
      const edge = scene.edges.find((e) => e.path === subjectEdge);
      if (edge) for (const id of [edge.from, edge.to, ...edge.targetPair ?? []]) kin.add(id);
    } else if (subjectCard) for (const id of cardWithKin(scene.edges, subjectCard)) kin.add(id);
    for (const card of scene.layout.cards)
      cards.set(card.id, settled && !subjectEdge && card.id === subjectCard ? "active" : !kin.size || kin.has(card.id) ? "idle" : quietest);
    for (const edge of scene.edges) {
      if (subjectEdge) edges.set(edge.path, edge.path === subjectEdge ? "active" : faintest);
      else if (subjectCard)
        edges.set(
          edge.path,
          edgeTouches(edge, subjectCard) ? !hoveredInsideSubjectSet || edge.path === hoveredInsideSubjectSet ? "active" : "rest" : faintest
        );
      else edges.set(edge.path, "rest");
    }
    const subject = subjectCard || subjectEdge;
    for (const nub of scene.nubs)
      nubs.set(nub.id, !subject ? "active" : nub.id === subjectCard ? "active" : kin.has(nub.id) ? "rest" : faintest);
    return { cards, edges, nubs, preview, settled };
  }

  // src/component-patterns/universe-map.ts
  var SVG2 = "http://www.w3.org/2000/svg";
  var MAX_DISPLAY_COUNT3 = 9;
  var DESCRIPTIONS_DRAWN_WITHIN_A_LINE_ALLOWANCE = ["frame", "factor", "option"];
  function optionStats(model, optionId) {
    const ordering = model.orderingFrameId.split(":").slice(1).join(":");
    const value = optionId.split(":").pop();
    const elements = model.entities.filter((e) => e.kind === "element" && (e.frameValues[ordering] ?? e.raw[ordering]) === value);
    const ids = new Set(elements.map((e) => e.id));
    const artifacts = model.entities.filter(
      (e) => e.kind === "artifact" && model.connections.some((c) => c.kind === "composition" && c.from === e.id && ids.has(c.to))
    );
    return { artifacts: artifacts.length, elements: elements.length };
  }
  function universeMap(scene, model, actions, measure) {
    const root = document.createElement("div");
    root.className = "world";
    const wires = document.createElementNS(SVG2, "svg");
    wires.classList.add("wires");
    wires.setAttribute("width", String(scene.bounds.x + scene.bounds.w + tokenNumber("--kb-scene-margin")));
    wires.setAttribute("height", String(scene.bounds.y + scene.bounds.h + tokenNumber("--kb-scene-margin")));
    root.append(wires);
    const labelsLayer = document.createElementNS(SVG2, "svg");
    labelsLayer.classList.add("labels-layer");
    labelsLayer.setAttribute("width", wires.getAttribute("width"));
    labelsLayer.setAttribute("height", wires.getAttribute("height"));
    const cards = /* @__PURE__ */ new Map();
    const edges = /* @__PURE__ */ new Map();
    const labels = /* @__PURE__ */ new Map();
    const labelShapes = /* @__PURE__ */ new Map();
    const named = byId(model);
    const marks = marksOf(model);
    const markOfBoundary = (id) => {
      const concept = named.get(id);
      if (!concept) return null;
      return concept.kind === "option" ? marks.value(concept.frameId ?? "", concept.sourceId, "frame") : marks.frame(concept.sourceId, concept.kind);
    };
    for (const boundary of scene.layout.boundaries) {
      const section2 = document.createElement("section");
      section2.className = "boundary";
      section2.dataset.role = boundary.role;
      section2.dataset.id = boundary.id;
      section2.style.left = `${boundary.x}px`;
      section2.style.top = `${boundary.y}px`;
      section2.style.width = `${boundary.w}px`;
      section2.style.height = `${boundary.h}px`;
      if (boundary.title) {
        const heading = document.createElement("button");
        heading.type = "button";
        heading.className = "boundary-title";
        heading.dataset.part = "heading";
        heading.dataset.boundary = boundary.id;
        const mark = markOfBoundary(boundary.id);
        if (mark) heading.append(markIcon(mark));
        const text = document.createElement("span");
        text.textContent = boundary.title;
        heading.append(text);
        heading.addEventListener("click", (event) => {
          event.stopPropagation();
          actions.selectEntity(boundary.id);
        });
        section2.append(heading);
      }
      if (boundary.caption) {
        const caption = document.createElement("p");
        caption.className = "boundary-caption";
        caption.dataset.part = "heading";
        caption.textContent = boundary.caption;
        section2.append(caption);
      }
      root.append(section2);
    }
    for (const note of scene.layout.notes) {
      const said = document.createElement("p");
      said.className = "boundary-note";
      said.dataset.boundary = note.scopeId;
      said.style.left = `${note.x}px`;
      said.style.top = `${note.y}px`;
      said.style.width = `${note.w}px`;
      said.style.height = `${note.h}px`;
      said.textContent = note.text;
      root.append(said);
    }
    for (const edge of scene.edges) {
      if (!edge.drawn) continue;
      const group = document.createElementNS(SVG2, "g");
      group.dataset.connection = edge.path;
      group.dataset.emphasis = "rest";
      const hit = document.createElementNS(SVG2, "path");
      hit.setAttribute("d", edge.d);
      hit.classList.add("wire-hit");
      hit.setAttribute("role", "button");
      hit.setAttribute("tabindex", "0");
      hit.setAttribute(
        "aria-label",
        `${human(edge.from.split(":").pop() ?? "")} to ${human(edge.to.split(":").pop() ?? "")}, ${edge.sources?.length ?? 1} connections`
      );
      const wire = document.createElementNS(SVG2, "path");
      wire.setAttribute("d", edge.d);
      wire.classList.add("wire");
      wire.dataset.paint = edge.paint;
      wire.dataset.dash = edge.dash;
      group.append(hit, wire);
      if (edge.ordered && edge.points.length > 1) {
        const end = edge.points[edge.points.length - 1];
        const before = edge.points[edge.points.length - 2];
        const dx = Math.sign(end.x - before.x);
        const dy = Math.sign(end.y - before.y) || (dx ? 0 : 1);
        const size = tokenNumber("--kb-space-2");
        const tip = dy ? [end, { x: end.x - size / 2, y: end.y - dy * size }, { x: end.x + size / 2, y: end.y - dy * size }] : [end, { x: end.x - dx * size, y: end.y - size / 2 }, { x: end.x - dx * size, y: end.y + size / 2 }];
        const head = document.createElementNS(SVG2, "polygon");
        head.setAttribute("points", tip.map((p) => `${p.x},${p.y}`).join(" "));
        head.classList.add("arrowhead");
        head.dataset.paint = edge.paint;
        const holding = holdingDrawn(edge);
        if (holding) head.dataset.holding = holding;
        group.append(head);
      }
      const activate = (event) => {
        event.stopPropagation();
        actions.selectConnection(edge.path);
      };
      hit.addEventListener("click", activate);
      hit.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate(event);
        }
      });
      hit.addEventListener("pointerenter", () => actions.hover(edge.path));
      hit.addEventListener("pointerleave", () => actions.hover(""));
      wires.append(group);
      edges.set(edge.path, group);
    }
    const nameOf = (id) => named.get(id)?.label ?? human(id.split(":").pop() ?? id);
    const endsOfEachEdge = /* @__PURE__ */ new Map();
    for (const edge of scene.edges)
      endsOfEachEdge.set(
        edge.path,
        edge.targetPair ? `${nameOf(edge.from)} · ${nameOf(edge.targetPair[0])} and ${nameOf(edge.targetPair[1])}` : `${nameOf(edge.from)} · ${nameOf(edge.to)}`
      );
    for (const label of scene.labels) {
      const group = document.createElementNS(SVG2, "g");
      group.dataset.label = label.edge;
      const leader = document.createElementNS(SVG2, "path");
      leader.setAttribute("d", `M ${label.anchor.x} ${label.anchor.y} L ${label.box.x + label.box.w / 2} ${label.box.y + label.box.h / 2}`);
      leader.classList.add("leader");
      const holder = document.createElementNS(SVG2, "foreignObject");
      holder.setAttribute("x", String(label.box.x));
      holder.setAttribute("y", String(label.box.y));
      holder.setAttribute("width", String(label.box.w));
      holder.setAttribute("height", String(label.box.h));
      const button = document.createElement("button");
      button.type = "button";
      button.className = "label";
      button.dataset.part = "label";
      button.textContent = label.text;
      button.setAttribute("aria-label", `${human(label.edge)}: ${label.text}`);
      button.title = endsOfEachEdge.get(label.edge) ?? "";
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        actions.selectConnection(label.edge);
      });
      button.addEventListener("pointerenter", () => actions.hover(label.edge));
      button.addEventListener("pointerleave", () => actions.hover(""));
      holder.append(button);
      group.append(leader, holder);
      labelsLayer.append(group);
      labels.set(label.edge, group);
      labelShapes.set(label.edge, {
        text: label.text,
        anchor: label.anchor,
        centre: { x: label.box.x + label.box.w / 2, y: label.box.y + label.box.h / 2 },
        holder,
        leader
      });
    }
    const ownerRoles = roleOfTheBoundaryEachCardStandsIn(scene.layout);
    const clampedDescriptions = [];
    for (const card of scene.layout.cards) {
      const element = card.kind === "option" ? optionCard(card, model, optionStats(model, card.id), actions.selectEntity) : entityCard(card, model, actions.selectEntity, measure);
      const ownerRole = ownerRoles.get(card.id);
      if (ownerRole) element.dataset.ownerRole = ownerRole;
      element.addEventListener("pointerenter", () => actions.hover(card.id));
      element.addEventListener("pointerleave", () => actions.hover(""));
      cards.set(card.id, element);
      if (DESCRIPTIONS_DRAWN_WITHIN_A_LINE_ALLOWANCE.includes(card.kind)) {
        const said = element.querySelector(".card-subtitle");
        if (said) clampedDescriptions.push(said);
      }
      root.append(element);
    }
    root.append(labelsLayer);
    const nubNodes = /* @__PURE__ */ new Map();
    let nubTreatment = /* @__PURE__ */ new Map();
    function dressNub(node, treatment) {
      node.dataset.emphasis = treatment;
      node.style.opacity = treatment === "hidden" ? "0" : treatment === "rest" ? String(tokenNumber("--kb-connection-opacity-idle")) : "1";
      node.style.pointerEvents = treatment === "hidden" ? "none" : "";
    }
    const countScale = (zoom) => grow(zoom, "--kb-count-zoom-growth");
    function setAttributeIfDifferent(node, name, value) {
      if (node.getAttribute(name) !== value) node.setAttribute(name, value);
    }
    function paintLabelBoxes(zoom) {
      for (const shape of labelShapes.values()) {
        const box = labelBox(shape.text, shape.centre, zoom);
        setAttributeIfDifferent(shape.holder, "x", String(box.x));
        setAttributeIfDifferent(shape.holder, "y", String(box.y));
        setAttributeIfDifferent(shape.holder, "width", String(box.w));
        setAttributeIfDifferent(shape.holder, "height", String(box.h));
        setAttributeIfDifferent(shape.leader, "d", `M ${shape.anchor.x} ${shape.anchor.y} L ${box.x + box.w / 2} ${box.y + box.h / 2}`);
      }
    }
    function replaceLabels(zoom) {
      for (const placed of labelLayer(scene.layout, scene.edges, scene.labelCandidates, zoom)) {
        const shape = labelShapes.get(placed.edge);
        if (!shape) continue;
        shape.anchor = placed.anchor;
        shape.centre = { x: placed.box.x + placed.box.w / 2, y: placed.box.y + placed.box.h / 2 };
      }
    }
    function paintNubs(placed, zoom) {
      for (const node of nubNodes.values()) node.remove();
      nubNodes.clear();
      for (const nub of placed) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "count";
        button.dataset.part = "count";
        button.style.setProperty("--zoom-scale", String(countScale(zoom)));
        button.textContent = nub.count > MAX_DISPLAY_COUNT3 ? `${MAX_DISPLAY_COUNT3}+` : String(nub.count);
        button.setAttribute("aria-label", `${human(nub.id.split(":").pop() ?? "")}: ${nub.count} connections`);
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          actions.selectConnection(`nub:${nub.id}`);
        });
        const host2 = cards.get(nub.id);
        if (nub.inset && host2) {
          button.classList.add("count-inset");
          host2.append(button);
          button.dataset.nub = nub.id;
          nubNodes.set(nub.id, button);
        } else {
          const group = document.createElementNS(SVG2, "g");
          const line = document.createElementNS(SVG2, "path");
          line.setAttribute("d", `M ${nub.from.x} ${nub.from.y} L ${nub.box.x + nub.box.w / 2} ${nub.box.y + nub.box.h / 2}`);
          line.style.setProperty("--zoom-scale", String(countScale(zoom)));
          line.classList.add("nub-line");
          const holder = document.createElementNS(SVG2, "foreignObject");
          holder.setAttribute("x", String(nub.box.x));
          holder.setAttribute("y", String(nub.box.y));
          holder.setAttribute("width", String(nub.box.w));
          holder.setAttribute("height", String(nub.box.h));
          holder.append(button);
          group.append(line, holder);
          wires.append(group);
          group.dataset.nub = nub.id;
          nubNodes.set(nub.id, group);
        }
      }
      for (const [id, node] of nubNodes) dressNub(node, nubTreatment.get(id) ?? "active");
    }
    let nubZoom = scene.zoom;
    paintNubs(scene.nubs, nubZoom);
    let labelGrowth = labelScale(scene.zoom);
    let describedAtHeadingScale = Number.NaN;
    function tellTheReaderWhateverIsClipped(headingScale) {
      let measured = false;
      for (const said of clampedDescriptions) {
        if (!said.clientHeight) continue;
        measured = true;
        if (said.scrollHeight > said.clientHeight) said.title = said.textContent ?? "";
        else said.removeAttribute("title");
      }
      if (measured) describedAtHeadingScale = headingScale;
    }
    function applyCamera(camera) {
      root.style.transform = `translate(${camera.x}px,${camera.y}px) scale(${camera.z})`;
      root.style.setProperty("--boundary-scale", String(boundaryScale(camera.z)));
      const headingScale = cardHeadingScale(camera.z);
      root.style.setProperty("--card-heading-scale", String(headingScale));
      root.dataset.headingGrown = String(headingScale !== 1);
      if (clampedDescriptions.length && headingScale !== describedAtHeadingScale) tellTheReaderWhateverIsClipped(headingScale);
      const scale = labelScale(camera.z);
      for (const group of labels.values())
        for (const node of group.querySelectorAll("button,.leader"))
          node.style.setProperty("--zoom-scale", String(scale));
      if (scene.labelCandidates.length && scale !== labelGrowth) {
        labelGrowth = scale;
        replaceLabels(camera.z);
      }
      paintLabelBoxes(camera.z);
      if (scene.nubs.length && camera.z !== nubZoom) {
        nubZoom = camera.z;
        paintNubs(nubLayer(scene.layout, scene.edges, nubZoom), nubZoom);
      }
    }
    function highlight(selection, hover) {
      const shown = emphasise(scene, selection, hover);
      const asState = { active: "selected", idle: "idle", hushed: "hushed", dimmed: "dimmed" };
      for (const [id, element] of cards) setCardState(element, asState[shown.cards.get(id) ?? "idle"], id === shown.preview);
      for (const [path, group] of edges) {
        const edge = scene.edges.find((e) => e.path === path);
        if (!edge) continue;
        const treatment = shown.edges.get(path) ?? "rest";
        const emphasisHold = edge.emphasized && treatment !== "hidden" && !shown.settled;
        group.dataset.emphasis = treatment;
        group.style.opacity = treatment === "active" || emphasisHold ? "1" : treatment === "hidden" ? "0" : String(tokenNumber("--kb-connection-opacity-idle"));
        group.style.pointerEvents = treatment === "hidden" ? "none" : "";
        const wire = group.querySelector(".wire");
        if (wire)
          wire.style.strokeWidth = treatment === "active" ? String(tokenNumber("--kb-connection-stroke-selected")) : edge.emphasized ? String(tokenNumber("--kb-connection-stroke-preview")) : "";
      }
      nubTreatment = shown.nubs;
      for (const [id, node] of nubNodes) dressNub(node, shown.nubs.get(id) ?? "active");
      for (const [path, group] of labels) {
        const treatment = shown.edges.get(path) ?? "rest";
        group.style.opacity = treatment === "hidden" ? "0" : treatment === "active" ? "1" : String(tokenNumber("--kb-connection-opacity-label-faint"));
        group.style.pointerEvents = treatment === "hidden" ? "none" : "";
      }
    }
    function drawnBounds() {
      const origin = root.getBoundingClientRect();
      const scale = new DOMMatrixReadOnly(getComputedStyle(root).transform).a || 1;
      const boxes = [...root.querySelectorAll(".boundary,.boundary-title,.card")].map((element) => element.getBoundingClientRect()).filter((box) => box.width && box.height);
      if (!boxes.length) return scene.bounds;
      const pad = tokenNumber("--kb-scene-margin");
      const x = Math.min(...boxes.map((b) => b.left - origin.left)) / scale - pad;
      const y = Math.min(...boxes.map((b) => b.top - origin.top)) / scale - pad;
      return {
        x,
        y,
        w: Math.max(...boxes.map((b) => b.right - origin.left)) / scale + pad - x,
        h: Math.max(...boxes.map((b) => b.bottom - origin.top)) / scale + pad - y
      };
    }
    return { root, applyCamera, highlight, cardElement: (id) => cards.get(id), drawnBounds };
  }

  // src/component-elements/icon-button.ts
  function iconButton(name, label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", label);
    button.title = label;
    button.append(icon(name));
    button.addEventListener("click", action);
    return button;
  }
  function labelledButton(name, label, action) {
    const button = document.createElement("button");
    button.type = "button";
    if (name) button.append(icon(name));
    const text = document.createElement("span");
    text.textContent = label;
    button.append(text);
    button.addEventListener("click", action);
    return button;
  }

  // src/component-elements/panel.ts
  function panel(className, label, onClose) {
    const root = document.createElement("aside");
    root.className = `panel ${className}`;
    root.setAttribute("aria-label", label);
    const head = document.createElement("header");
    head.className = "panel-head";
    const title = document.createElement("strong");
    const close = iconButton("close", "Close", onClose);
    close.classList.add("close");
    head.append(title, close);
    const body = document.createElement("div");
    body.className = "panel-body";
    root.append(head, body);
    return { root, head, body, title };
  }

  // src/component-elements/segmented.ts
  function segmented(label, choices, value, onChange, className = "segment") {
    const group = document.createElement("div");
    group.className = className;
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", label);
    for (const choice of choices) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.value = choice.value;
      button.setAttribute("aria-pressed", String(choice.value === value));
      if (choice.tooltip) button.title = choice.tooltip;
      if (choice.content) button.append(choice.content());
      const text = document.createElement("span");
      text.textContent = choice.label;
      button.append(text);
      if (choice.description) {
        button.setAttribute("aria-label", `${choice.label}: ${choice.description}`);
        const small = document.createElement("small");
        small.textContent = choice.description;
        text.append(small);
      }
      button.addEventListener("click", () => onChange(choice.value));
      group.append(button);
    }
    return group;
  }

  // src/component-elements/relation-glyph.ts
  var SVG3 = "http://www.w3.org/2000/svg";
  function drawnWire(drawing, reading) {
    const span = tokenNumber("--kb-size-sm");
    const height = tokenNumber("--kb-icon-base");
    const middle = height / 2;
    const svg = document.createElementNS(SVG3, "svg");
    svg.setAttribute("viewBox", `0 0 ${span} ${height}`);
    svg.setAttribute("class", "glyph-wire");
    svg.setAttribute("role", "img");
    const title = document.createElementNS(SVG3, "title");
    title.textContent = reading;
    svg.append(title);
    const wire = document.createElementNS(SVG3, "path");
    wire.setAttribute("d", `M 0 ${middle} L ${span} ${middle}`);
    wire.classList.add("wire");
    wire.dataset.paint = drawing.paint;
    wire.dataset.dash = drawing.requirement === "situational" ? "situational" : "none";
    svg.append(wire);
    if (drawing.ordered) {
      const tip = tokenNumber("--kb-space-2");
      const head = document.createElementNS(SVG3, "polygon");
      head.setAttribute("points", `${span},${middle} ${span - tip},${middle - tip / 2} ${span - tip},${middle + tip / 2}`);
      head.classList.add("arrowhead");
      head.dataset.paint = drawing.paint;
      svg.append(head);
    }
    return svg;
  }
  function holdingGlyph(holding) {
    const side = tokenNumber("--kb-icon-base");
    const middle = side / 2;
    const svg = document.createElementNS(SVG3, "svg");
    svg.setAttribute("viewBox", `0 0 ${side} ${side}`);
    svg.setAttribute("class", "holding-glyph");
    svg.setAttribute("aria-hidden", "true");
    const mark = document.createElementNS(SVG3, "polygon");
    mark.setAttribute("points", `0,${middle / 2} ${side},${middle} 0,${middle + middle / 2}`);
    mark.dataset.holding = holding;
    svg.append(mark);
    return svg;
  }
  function relationGlyph(drawing, from, to, reading) {
    const glyph = document.createElement("div");
    glyph.className = "relation-glyph";
    glyph.dataset.paint = drawing.paint;
    const target = document.createElement("span");
    target.className = "glyph-target";
    target.append(drawnWire(drawing, reading), to);
    glyph.append(from, target);
    return glyph;
  }

  // src/component-elements/disclosure-list.ts
  var DETAIL_LIMIT = 3;
  var RESULT_LIMIT = 5;
  function disclosureList(items, limit = DETAIL_LIMIT) {
    const group = document.createElement("div");
    group.append(...items);
    if (items.length <= limit) return group;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "show-all";
    const render = (expanded) => {
      items.slice(limit).forEach((item) => {
        item.hidden = !expanded;
      });
      toggle.textContent = expanded ? "Show fewer" : `Show all ${items.length}`;
      toggle.setAttribute("aria-expanded", String(expanded));
    };
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      render(toggle.getAttribute("aria-expanded") !== "true");
    });
    group.append(toggle);
    render(false);
    return group;
  }

  // src/component-patterns/detail-copy.ts
  function section(title, body) {
    if (!body.length) return null;
    const element = document.createElement("section");
    element.className = "section";
    const heading = document.createElement("h3");
    heading.textContent = title;
    element.append(heading, ...body);
    return element;
  }
  function paragraph(text, className) {
    const p = document.createElement("p");
    if (className) p.className = className;
    p.textContent = text;
    return p;
  }
  function frameName(context, id) {
    const span = document.createElement("span");
    span.className = "frame-name";
    span.append(markIcon(marksOf(context.model).frame(id)));
    const text = document.createElement("span");
    text.textContent = human(id);
    span.append(text);
    return span;
  }
  function conditions(context, value) {
    const box = document.createElement("div");
    box.className = "conditions";
    const entries = Object.entries(value ?? {});
    entries.forEach(([key, inner], index) => {
      if (index) {
        const joiner = document.createElement("div");
        joiner.className = "conjunction";
        joiner.textContent = "and";
        box.append(joiner);
      }
      const row = document.createElement("div");
      row.append(frameName(context, key));
      if (Array.isArray(inner)) {
        const strong = document.createElement("strong");
        inner.forEach((item, position) => {
          if (position) {
            const or = document.createElement("em");
            or.className = "conjunction";
            or.textContent = " or ";
            strong.append(or);
          }
          strong.append(document.createTextNode(human(String(item))));
        });
        row.append(strong);
      } else if (inner && typeof inner === "object") row.append(conditions(context, inner));
      else {
        const strong = document.createElement("strong");
        strong.textContent = String(inner);
        row.append(strong);
      }
      box.append(row);
    });
    return box;
  }
  function reference(context, id, detail = "", lead) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "reference";
    button.dataset.target = id;
    const label = document.createElement("span");
    if (lead) label.append(lead);
    label.append(document.createTextNode(nameOfEntity(context, id)));
    button.append(label);
    if (detail) {
      const small = document.createElement("small");
      small.textContent = detail;
      button.append(small);
    }
    button.append(icon("chevron"));
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      context.select(id);
    });
    return button;
  }
  function inlineReference(context, id) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "inline-reference";
    button.dataset.target = id;
    button.textContent = nameOfEntity(context, id);
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      context.select(id);
    });
    return button;
  }
  var COPY_DEFINITION = "Copy definition";
  function sourceDisclosure(value) {
    const details = document.createElement("details");
    details.className = "source";
    const summary = document.createElement("summary");
    summary.textContent = "Source definition";
    const definition = JSON.stringify(value, (key, inner) => ["code", "path", "type"].includes(key) ? void 0 : inner, 2);
    const block = document.createElement("div");
    block.className = "code-block";
    const copy = iconButton("copy", COPY_DEFINITION, () => void navigator.clipboard?.writeText(definition));
    copy.title = COPY_DEFINITION;
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    code.textContent = definition;
    pre.append(code);
    block.append(copy, pre);
    details.append(summary, block);
    return details;
  }
  var nameOfEntity = (context, id) => context.named.get(id)?.label ?? human(id.split(":").pop() ?? id);
  var countOf = (many, noun, plural = `${noun}s`) => `${many} ${many === 1 ? noun : plural}`;
  var countingWhatTheRowsAre = (context, targets) => {
    const kinds = new Set(targets.map((target) => context.named.get(target)?.kind).filter(Boolean));
    return countOf(targets.length, kinds.size === 1 ? [...kinds][0] : "entry");
  };
  function groupBox(heading, body) {
    const block = document.createElement("div");
    block.className = "group";
    const stated = document.createElement("h4");
    stated.textContent = heading;
    block.append(stated, ...body);
    return block;
  }
  function semanticRow(context, target) {
    const entity = context.named.get(target);
    const entry = document.createElement("div");
    entry.className = "entry semantic-row";
    entry.dataset.semanticId = target;
    const name = document.createElement("p");
    name.className = "semantic-name";
    name.textContent = nameOfEntity(context, target);
    entry.append(name);
    if (entity?.description.trim()) {
      const description = document.createElement("p");
      description.className = "semantic-description";
      description.textContent = entity.description;
      entry.append(description);
    }
    return entry;
  }
  function semanticGroup(context, targets, disclosureLimit) {
    const rows = targets.map((target) => semanticRow(context, target));
    if (disclosureLimit === void 0) return groupBox(countingWhatTheRowsAre(context, targets), rows);
    const list = disclosureList(rows, disclosureLimit);
    list.className = "semantic-list";
    return groupBox(countingWhatTheRowsAre(context, targets), [list]);
  }
  function listedGroup(heading, names) {
    return groupBox(
      heading,
      names.map((name) => {
        const entry = document.createElement("div");
        entry.className = "entry";
        entry.textContent = name;
        return entry;
      })
    );
  }
  function rowsGroup(context, targets, rows) {
    return groupBox(countingWhatTheRowsAre(context, targets), [disclosureList(rows)]);
  }
  function compositionMemberRow(context, row) {
    const entry = document.createElement("div");
    entry.className = "entry";
    entry.dataset.holding = row.holding;
    const destination = row.destination ? `Kept in ${nameOfEntity(context, row.destination)}` : "";
    entry.append(reference(context, row.target, destination, holdingGlyph(row.holding)));
    return entry;
  }
  function gatingBlock(context, gate) {
    if (!gate.conditionTitle) return null;
    const body = [conditions(context, gate.when)];
    if (gate.fallback) body.push(paragraph(gate.fallback));
    return section(gate.conditionTitle, body);
  }
  function compositionGroupBlock(context, group) {
    const heading = `${group.predicate} · ${countingWhatTheRowsAre(
      context,
      group.rows.map((row) => row.target)
    )}`;
    const gate = gatingBlock(context, group);
    return groupBox(heading, [...gate ? [gate] : [], disclosureList(group.rows.map((row) => compositionMemberRow(context, row)))]);
  }
  function guidanceDisclosure(context, entries) {
    if (!entries.length) return null;
    const details = document.createElement("details");
    details.className = "guidance";
    const summary = document.createElement("summary");
    const heading = document.createElement("span");
    heading.textContent = GUIDANCE_HEADING;
    const count = document.createElement("span");
    count.className = "muted";
    count.textContent = ` · ${guidanceCountCopy(entries.length)}`;
    summary.append(heading, count);
    details.append(summary);
    for (const entry of entries) {
      const held = document.createElement("div");
      held.className = "entry claim";
      held.append(paragraph(entry.claim));
      if (entry.when && Object.keys(entry.when).length) {
        const block = section("Applies when", [conditions(context, entry.when)]);
        if (block) held.append(block);
      }
      details.append(held);
    }
    return details;
  }
  function relationStatement(context, edge, subject = edge.from, linked = true) {
    const statement = paragraph("", "statement");
    const kinds = relationKinds(context.model);
    const kind = kinds.find((k) => k.id === edge.kind);
    const item = (id) => linked ? inlineReference(context, id) : document.createTextNode(context.model.entities.find((e) => e.id === id)?.label ?? human(id));
    const phrasing = relationPhrasing(edge, kind, subject);
    if (phrasing) {
      const predicate2 = document.createElement("span");
      predicate2.className = "muted";
      predicate2.textContent = phrasing.phrase;
      statement.append(item(phrasing.subject), document.createTextNode(" "), predicate2, document.createTextNode(" "), item(phrasing.object));
      return statement;
    }
    const from = context.model.entities.find((e) => e.id === edge.from);
    const to = context.model.entities.find((e) => e.id === edge.to);
    if (edge.kind === "feeds") {
      statement.append(
        document.createTextNode("Knowledge from "),
        item(edge.from),
        document.createTextNode(" can inform "),
        item(edge.to),
        document.createTextNode(".")
      );
      return statement;
    }
    if (edge.kind === "distinct-from") {
      statement.append(
        item(edge.from),
        document.createTextNode(" and "),
        item(edge.to),
        document.createTextNode(` ${distinctFromCopy(from, to)}. One should not substitute for the other.`)
      );
      return statement;
    }
    const predicate = document.createElement("span");
    predicate.className = "muted";
    predicate.textContent = friendly(edge.kind, kinds);
    statement.append(item(edge.from), document.createTextNode(" "), predicate, document.createTextNode(" "), item(edge.to));
    return statement;
  }
  function relationRestrictions(context, edge) {
    const raw = edge.raw ?? {};
    const blocks = [];
    if (edge.when) {
      const block = section("Applies when", [conditions(context, edge.when)]);
      if (block) blocks.push(block);
    }
    if (raw.gate) {
      const block = section("Conditions", [conditions(context, raw.gate)]);
      if (block) blocks.push(block);
    }
    if (raw.legality) {
      const block = section("Use of this connection", [paragraph(legalityCopy(raw.legality) ?? "")]);
      if (block) blocks.push(block);
    }
    if (raw.freeze) {
      const block = section("Change rule", [paragraph(freezeCopy(raw.freeze) ?? "")]);
      if (block) blocks.push(block);
    }
    return blocks;
  }
  function relationRow(context, edge, subject, heading = true) {
    const row = document.createElement("div");
    row.className = "relation entry";
    const kinds = relationKinds(context.model);
    const kind = kinds.find((k) => k.id === edge.kind);
    if (subject) {
      const other = edge.from === subject ? edge.to : edge.from;
      const own = context.model.entities.find((e) => e.id === subject)?.label ?? human(subject);
      const copy = relationPhrasing(edge, kind, other);
      let phrase = copy ? copy.phrase : "";
      if (!copy && edge.kind === "feeds") phrase = edge.from === subject ? "Can be informed by knowledge from" : "Knowledge here can inform";
      if (!copy && edge.kind === "distinct-from") phrase = "Distinct from";
      if (!phrase) row.append(relationStatement(context, edge, subject));
      else if (heading) row.append(reference(context, other, `${phrase} ${own}`));
      else row.append(paragraph(phrase, "muted"));
    } else row.append(relationStatement(context, edge));
    if (edge.kind === "distinct-from") {
      const from = context.model.entities.find((e) => e.id === edge.from);
      const to = context.model.entities.find((e) => e.id === edge.to);
      const meaning = document.createElement("details");
      meaning.className = "meaning";
      const summary = document.createElement("summary");
      summary.textContent = "Meaning";
      meaning.append(summary, paragraph(`These ${distinctFromCopy(from, to)}; one should not substitute for the other.`));
      row.append(meaning);
    }
    row.append(...relationRestrictions(context, edge));
    return row;
  }
  function sharedElementRow(context, provenance) {
    const row = document.createElement("div");
    row.className = "relation-block";
    const element = provenance.composition[0]?.to;
    if (!element) return row;
    const heading = document.createElement("h3");
    heading.append(inlineReference(context, element));
    row.append(heading);
    const members = provenance.composition.map((entry) => ({
      target: entry.from,
      answer: entry.to,
      strength: entry.strength,
      mode: entry.mode,
      when: entry.when
    }));
    for (const group of compositionGroups(members, context.owners)) row.append(compositionGroupBlock(context, group));
    return row;
  }

  // src/lib/guidance-reading.ts
  var guidanceEntries = (model) => model.guidance?.entries ?? [];
  var guidanceFor = (model, subject) => guidanceEntries(model).filter((entry) => entry.subject === subject);

  // src/component-patterns/detail-overlay.ts
  var SECTION_TITLES = { contents: ["Contents", "Used in", "Options"], related: ["Related knowledge"] };
  function facts(rows) {
    const list = document.createElement("dl");
    list.className = "facts";
    for (const [term, value] of rows) {
      const row = document.createElement("div");
      const dt = document.createElement("dt");
      dt.textContent = term;
      const dd = document.createElement("dd");
      dd.textContent = value;
      row.append(dt, dd);
      list.append(row);
    }
    return list;
  }
  function detailOverlay(model, subject, close, select) {
    const context = {
      model,
      select,
      owners: answerOwners(model.connections.filter((c) => c.kind === "composition")),
      named: byId(model)
    };
    const entity = model.entities.find((e) => e.id === subject);
    const rule = model.rules.find((r) => r.id === subject);
    const surface = panel("detail", "Definition details", close);
    surface.title.textContent = entity?.label ?? "No artifact needed";
    const body = surface.body;
    if (!entity) body.append(paragraph("Rule", "detail-kind"));
    if (entity?.description) body.append(paragraph(entity.description, "detail-question"));
    const ordering = model.orderingFrameId.split(":").slice(1).join(":");
    const composition = model.connections.filter((c) => c.kind === "composition");
    if (entity?.kind === "element") {
      body.append(
        facts([
          [human(ordering), human(String(entity.frameValues[ordering] ?? entity.raw[ordering] ?? ""))],
          ["Answers", cardinalityDetail(entity.raw.cardinality)]
        ])
      );
      if (entity.raw.gate) {
        const block2 = section("Applies when", [conditions(context, entity.raw.gate)]);
        if (block2) body.append(block2);
      }
      const advice = guidanceDisclosure(context, guidanceFor(model, entity.id));
      if (advice) body.append(advice);
      const usedIn = composition.filter((c) => c.to === entity.id).map((c) => ({ target: c.from, answer: c.to, strength: c.strength, mode: c.mode, when: c.when }));
      const block = section(
        "Used in",
        compositionGroups(usedIn, context.owners).map((group) => compositionGroupBlock(context, group))
      );
      if (block) body.append(block);
    } else if (entity?.kind === "artifact") {
      const enablement = entity.raw.enablement ?? {};
      const helps = section("Helps you", [paragraph(String(enablement.action ?? ""), "detail-question")]);
      if (helps) body.append(helps);
      body.append(
        facts([
          ["Who uses it", String(enablement.actor ?? "")],
          ...enablement.timing ? [["When to use it", String(enablement.timing)]] : []
        ])
      );
      if (entity.raw.disabled_when) {
        const block = section("Do not use when", [conditions(context, entity.raw.disabled_when)]);
        if (block) body.append(block);
      }
      const advice = guidanceDisclosure(context, guidanceFor(model, entity.id));
      if (advice) body.append(advice);
      const members = composition.filter((c) => c.from === entity.id).map((c) => ({ target: c.to, from: c.from, strength: c.strength, mode: c.mode, when: c.when })).sort((left, right) => (left.strength === "core" ? 0 : 1) - (right.strength === "core" ? 0 : 1));
      const groups = compositionGroups(members, context.owners);
      const contents2 = section(
        "Contents",
        groups.map((group) => compositionGroupBlock(context, group))
      );
      if (contents2) body.append(contents2);
      if (entity.raw.alias?.form) {
        const block = section(entity.raw.alias.kind === "normative" ? "Externally defined format" : "Related format", [
          paragraph(String(entity.raw.alias.form))
        ]);
        if (block) body.append(block);
      }
    } else if (entity?.kind === "option") {
      const frame = model.entities.find((e) => e.id === entity.frameId);
      const values = model.entities.filter((e) => e.kind === "element" && (e.frameValues[ordering] ?? e.raw[ordering]) === entity.sourceId);
      const ids = new Set(values.map((e) => e.id));
      const owners = model.entities.filter((e) => e.kind === "artifact" && composition.some((c) => c.from === e.id && ids.has(c.to)));
      body.prepend(paragraph(frame ? `${frame.label} option` : "Option", "detail-kind"));
      body.append(
        facts([
          ["Artifacts", String(owners.length)],
          ["Elements", String(values.length)]
        ])
      );
      const block = section(
        "Elements here",
        values.length ? [
          semanticGroup(
            context,
            values.map((element) => element.id),
            2
          )
        ] : []
      );
      if (block) body.append(block);
    } else if (entity) {
      if (entity.raw.role) {
        const block = section("Role", [paragraph(roleCopy(entity.raw.role))]);
        if (block) body.append(block);
      }
      const options = model.entities.filter((e) => e.kind === "option" && e.id.startsWith(`option:${entity.sourceId}:`));
      if (options.length) {
        const block = section("Options", [
          semanticGroup(
            context,
            options.map((option) => option.id)
          )
        ]);
        if (block) body.append(block);
      }
      for (const [facet, values] of Object.entries(entity.raw.facets ?? {})) {
        const block = section(human(facet), [listedGroup(countOf(values.length, "option"), values.map(human))]);
        if (block) body.append(block);
      }
    } else if (rule) {
      const block = section("No artifact needed when", [conditions(context, rule.raw.when)]);
      if (block) body.append(block);
    }
    const relations = model.connections.filter((c) => c.kind !== "composition" && (c.from === subject || c.to === subject));
    if (relations.length) {
      const rows = relations.map((c) => relationRow(context, c, subject));
      const others = relations.map((c) => c.from === subject ? c.to : c.from);
      const block = section("Related knowledge", [rowsGroup(context, others, rows)]);
      if (block) body.append(block);
    }
    body.append(sourceDisclosure(entity?.raw ?? rule?.raw ?? {}));
    const blocks = [...body.querySelectorAll(":scope > .section")];
    const find = (titles) => blocks.find((block) => titles.includes(block.querySelector("h3")?.textContent ?? ""));
    const contents = find(SECTION_TITLES.contents);
    const related = find(SECTION_TITLES.related);
    if (contents || related) {
      const choices = [
        { value: "overview", label: "Overview" },
        ...contents ? [{ value: "contents", label: "Contents" }] : [],
        ...related ? [{ value: "related", label: "Related" }] : []
      ];
      const nav = segmented(
        "Detail sections",
        choices,
        "overview",
        (value) => {
          const target = value === "contents" ? contents : value === "related" ? related : null;
          body.scrollTop = target ? target.offsetTop - body.offsetTop : 0;
          for (const button of nav.querySelectorAll("button")) button.setAttribute("aria-pressed", String(button.dataset.value === value));
        },
        "sections"
      );
      surface.head.after(nav);
    }
    return { root: surface.root, subject };
  }

  // src/lib/connection-reading.ts
  var SHARED_ELEMENT_LABEL = "Shared element";
  var labelOfEntity = (model, id) => model.entities.find((entity) => entity.id === id)?.label ?? human(id.split(":").pop() ?? id);
  var endOf = (model, id) => ({ id, label: labelOfEntity(model, id) });
  var connectionDefining = (model, path) => path === void 0 ? void 0 : model.connections.find((connection) => connection.sourcePath === path);
  var appliesOnlySometimes = (strength) => strength === "situational" || strength === "mixed";
  var requirementAcross = (steps, own) => {
    const strengths = [own, ...steps.map((step) => step.strength)].filter((strength) => strength !== void 0);
    if (!strengths.length) return null;
    return strengths.some(appliesOnlySometimes) ? "situational" : "core";
  };
  function wireDrawingOf(model, provenance) {
    const steps = provenance.composition;
    if (provenance.source.label === SHARED_ELEMENT_LABEL) {
      const [owner, peer] = steps;
      if (!owner || !peer) return null;
      return {
        from: endOf(model, owner.from),
        to: endOf(model, peer.from),
        ordered: false,
        paint: "rolled",
        requirement: requirementAcross(steps, void 0)
      };
    }
    const connection = connectionDefining(model, provenance.source.path);
    if (!connection) return null;
    return {
      from: endOf(model, connection.from),
      to: endOf(model, connection.to),
      ordered: connection.ordered,
      paint: steps.length ? "rolled" : "element",
      requirement: requirementAcross(steps, connection.strength)
    };
  }
  function endsOfConnectionPanel(model, edge, provenances) {
    const anchor = edge.from;
    const others = /* @__PURE__ */ new Set();
    for (const provenance of provenances) {
      const drawing = wireDrawingOf(model, provenance);
      const ends = drawing ? [drawing.from.id, drawing.to.id] : [provenance.source.from, provenance.source.to];
      for (const id of ends) if (id !== anchor) others.add(id);
      if (others.size > 1) return { anchor, other: null };
    }
    return { anchor, other: others.size === 1 ? [...others][0] : null };
  }
  function definitionsBehind(model, provenances) {
    return provenances.flatMap((provenance) => {
      const direct = connectionDefining(model, provenance.source.path);
      if (direct) return [direct.raw];
      if (provenance.source.label !== SHARED_ELEMENT_LABEL) return [];
      return provenance.composition.map((step) => connectionDefining(model, step.path)).filter((step) => step !== void 0).map((step) => step.raw);
    });
  }

  // src/component-patterns/universe-overview.ts
  function universeStats(model) {
    const stats = document.createElement("div");
    stats.className = "stats";
    stats.setAttribute("aria-label", "Universe summary");
    const counts = [
      ["Artifacts", model.entities.filter((e) => e.kind === "artifact").length],
      ["Elements", model.entities.filter((e) => e.kind === "element").length],
      ["Frames", model.entities.filter((e) => e.kind === "frame").length],
      ["Factors", model.entities.filter((e) => e.kind === "factor").length],
      ["Relations", model.connections.filter((c) => c.kind !== "composition").length]
    ];
    for (const [label, count] of counts) {
      const item = document.createElement("span");
      const value = document.createElement("b");
      value.textContent = String(count);
      item.append(value, document.createTextNode(` ${label}`));
      stats.append(item);
    }
    return stats;
  }
  function universeOverview(model, close) {
    const scrim = document.createElement("div");
    scrim.className = "scrim";
    scrim.addEventListener("click", (event) => {
      event.stopPropagation();
      close();
    });
    const surface = panel("overview", "Universe overview", close);
    surface.root.querySelector(".panel-head")?.classList.add("overview-head");
    surface.title.textContent = model.universe.label;
    surface.head.append(universeStats(model));
    const overview = model.universe.overview ?? {};
    for (const [title, key] of [
      ["About", "covers"],
      ["Who it is for", "for"],
      ["Outside its scope", "excludes"]
    ]) {
      const block2 = section(title, overview[key] ? [paragraph(overview[key])] : []);
      if (block2) surface.body.append(block2);
    }
    const details = document.createElement("details");
    details.className = "source";
    const summary = document.createElement("summary");
    summary.textContent = "Definition information";
    const facts2 = document.createElement("dl");
    facts2.className = "facts";
    for (const [term, value] of [
      ["Version", String(model.universe.version)],
      ["Protocol", String(model.universe.conforms_to ?? model.protocolVersion)]
    ]) {
      const row = document.createElement("div");
      const dt = document.createElement("dt");
      dt.textContent = term;
      const dd = document.createElement("dd");
      dd.textContent = value;
      row.append(dt, dd);
      facts2.append(row);
    }
    details.append(summary, facts2);
    const statuses = model.source.statuses ?? [];
    const block = section(
      "Declared statuses",
      statuses.length ? [listedGroup(countOf(statuses.length, "status", "statuses"), statuses.map(human))] : []
    );
    if (block) details.append(block);
    surface.body.append(details);
    return { scrim, root: surface.root };
  }

  // src/component-patterns/chrome.ts
  function topBar(model, actions) {
    const root = document.createElement("div");
    root.className = "topbar";
    const identity = document.createElement("div");
    identity.className = "identity";
    const title = document.createElement("button");
    title.type = "button";
    title.className = "identity-title";
    title.title = "Open universe details";
    const name = document.createElement("strong");
    name.textContent = model.universe.label;
    title.append(name, icon("chevron-down"));
    title.addEventListener("click", (event) => {
      event.stopPropagation();
      actions.openOverview();
    });
    identity.append(title, universeStats(model));
    const tabs = document.createElement("div");
    tabs.className = "view-tabs";
    const renderTabs = (view) => {
      const group = segmented(
        "Map view",
        [
          { value: "frames", label: "Dimensions" },
          { value: "artifacts", label: "Artifacts" },
          { value: "elements", label: "Artifacts & Elements" }
        ],
        view,
        (value) => actions.setView(value)
      );
      tabs.replaceChildren(...group.childNodes);
    };
    const utilities = document.createElement("div");
    utilities.className = "utilities";
    const themeButton = iconButton("sun", "Use dark theme", actions.toggleTheme);
    themeButton.title = "Use dark theme";
    const shareButton = iconButton("share", "Export map", actions.toggleShare);
    shareButton.setAttribute("aria-expanded", "false");
    utilities.append(themeButton, shareButton);
    root.append(identity, tabs, utilities);
    const syncTheme = (effective) => {
      const label = effective === "light" ? "Use dark theme" : "Use light theme";
      themeButton.setAttribute("aria-label", label);
      themeButton.title = label;
      themeButton.replaceChildren(icon(effective === "light" ? "sun" : "moon"));
    };
    return { root, tabs, utilities, themeButton, shareButton, renderTabs, syncTheme };
  }
  function shareMenu(exportSvg) {
    const menu = document.createElement("div");
    menu.className = "share-menu";
    menu.setAttribute("aria-label", "Export map");
    const copyHeading = document.createElement("div");
    copyHeading.className = "menu-heading";
    copyHeading.textContent = "Copy";
    const copy = labelledButton("copy", "Copy image", () => {
    });
    copy.disabled = true;
    const downloadHeading = document.createElement("div");
    downloadHeading.className = "menu-heading";
    downloadHeading.textContent = "Download";
    const png = labelledButton("image", "PNG", () => {
    });
    png.disabled = true;
    png.querySelector("span")?.append(Object.assign(document.createElement("small"), { textContent: "Image" }));
    const svg = labelledButton("vector", "SVG", exportSvg);
    svg.querySelector("span")?.append(Object.assign(document.createElement("small"), { textContent: "Vector image" }));
    menu.append(copyHeading, copy, downloadHeading, png, svg);
    return menu;
  }
  var PERCENT = 100;
  function dock(actions) {
    const root = document.createElement("div");
    root.className = "dock";
    root.setAttribute("aria-label", "Map navigation");
    const first = document.createElement("div");
    first.className = "dock-group";
    first.append(iconButton("search", "Find an artifact or element", actions.search));
    const second = document.createElement("div");
    second.className = "dock-group";
    const mapToggle = labelledButton("map", "Map", actions.toggleMinimap);
    mapToggle.setAttribute("aria-expanded", "false");
    mapToggle.title = "Open Map";
    const readout = document.createElement("output");
    readout.className = "zoom-readout";
    const actual = document.createElement("button");
    actual.type = "button";
    actual.setAttribute("aria-label", "Reset zoom to 100%");
    actual.title = "Reset zoom to 100%";
    actual.append(readout);
    actual.addEventListener("click", actions.actualSize);
    second.append(
      mapToggle,
      iconButton("fit", "Fit map to view", actions.fit),
      iconButton("minus", "Zoom out", actions.zoomOut),
      actual,
      iconButton("plus", "Zoom in", actions.zoomIn)
    );
    root.append(first, second);
    return {
      root,
      mapToggle,
      readout,
      setZoom: (zoom) => readout.textContent = `${Math.round(zoom * PERCENT)}%`,
      setMinimapOpen: (open) => {
        mapToggle.setAttribute("aria-expanded", String(open));
        mapToggle.title = open ? "Close Map" : "Open Map";
      }
    };
  }
  var legendRowCopy = {
    direct: "Direct",
    rolled: "Rolled up",
    required: "Required",
    situational: "When applicable",
    mixed: "Both",
    owns: "Answer",
    links: "Reference"
  };
  var SVG4 = "http://www.w3.org/2000/svg";
  function legendSwatch() {
    const span = tokenNumber("--kb-legend-swatch-width");
    const height = tokenNumber("--kb-icon-base");
    const middle = height / 2;
    const svg = document.createElementNS(SVG4, "svg");
    svg.setAttribute("viewBox", `0 0 ${span} ${height}`);
    svg.setAttribute("class", "legend-swatch");
    svg.setAttribute("aria-hidden", "true");
    const mark = document.createElementNS(SVG4, "path");
    mark.setAttribute("d", `M 0 ${middle} L ${span} ${middle}`);
    svg.append(mark);
    return svg;
  }
  function legend(rows) {
    const root = document.createElement("div");
    root.className = "legend";
    for (const row of rows) {
      const item = document.createElement("span");
      item.dataset.key = row;
      const holding = LEGEND_ROW_HOLDING[row];
      item.append(holding ? holdingGlyph(holding) : legendSwatch());
      item.append(document.createTextNode(legendRowCopy[row]));
      root.append(item);
    }
    return root;
  }

  // src/component-patterns/connection-overlay.ts
  var readingOf = (drawing, requirement) => [legendRowCopy[drawing.paint === "rolled" ? "rolled" : "direct"], requirement].filter(Boolean).join(" · ");
  var requirementBehind = (drawing, connection) => {
    if (connection?.kind === "composition") return compositionDetails(connection).requirement;
    return drawing.requirement ? compositionDetails({ strength: drawing.requirement, when: null }).requirement : "";
  };
  function connectionOverlay(model, edge, close, select) {
    const context = {
      model,
      select,
      owners: answerOwners(model.connections.filter((c) => c.kind === "composition")),
      named: byId(model)
    };
    const surface = panel("detail", "Connection details", close);
    const anchor = edge.from;
    const provenances = edge.sources ?? [{ source: edge, composition: [] }];
    const ends = endsOfConnectionPanel(model, edge, provenances);
    surface.title.textContent = ends.other ? `${labelOfEntity(model, ends.anchor)} · ${labelOfEntity(model, ends.other)}` : labelOfEntity(model, ends.anchor);
    const shared = provenances.every((p) => p.source.label === "Shared element");
    const caption = paragraph(
      `${provenances.length} ${shared ? `shared ${provenances.length === 1 ? "element" : "elements"}` : provenances.length === 1 ? "connection" : "connections"}`,
      "detail-kind"
    );
    surface.body.append(caption);
    const rows = provenances.map((provenance) => {
      const source = provenance.source;
      if (source.label === "Shared element") return sharedElementRow(context, provenance);
      const connection = model.connections.find((c) => c.sourcePath === source.path);
      const inside = [];
      if (connection?.kind === "composition") {
        const gate = gatingBlock(context, { ...compositionDetails(connection), when: connection.when });
        if (gate) inside.push(gate);
      } else if (connection) inside.push(relationRow(context, connection, edge.nub ? anchor : connection.from, false));
      else inside.push(paragraph(`${human(source.from.split(":").pop() ?? "")} · ${source.label}`, "statement"));
      const drawing = wireDrawingOf(model, provenance);
      if (!drawing) {
        const unresolved = document.createElement("div");
        unresolved.className = "relation";
        unresolved.append(...inside);
        return unresolved;
      }
      const reading = readingOf(drawing, requirementBehind(drawing, connection));
      inside.unshift(relationGlyph(drawing, inlineReference(context, drawing.from.id), inlineReference(context, drawing.to.id), reading));
      return groupBox(reading, inside);
    });
    surface.body.append(disclosureList(rows));
    const definitions = definitionsBehind(model, provenances);
    if (definitions.length) surface.body.append(sourceDisclosure(definitions));
    return surface.root;
  }

  // src/component-elements/chip.ts
  function chip(value, label, pressed, glyph, toggle) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    button.dataset.value = value;
    button.setAttribute("aria-pressed", String(pressed));
    if (glyph) button.append(markIcon(glyph));
    const text = document.createElement("span");
    text.textContent = label;
    button.append(text);
    button.addEventListener("click", toggle);
    return button;
  }

  // src/component-elements/field.ts
  function field(label, control, glyph) {
    const wrapper = document.createElement("div");
    wrapper.className = "field";
    const heading = document.createElement("div");
    heading.className = "field-label";
    if (glyph) heading.append(glyph);
    const text = document.createElement("span");
    text.textContent = label;
    heading.append(text);
    wrapper.append(heading, control);
    return wrapper;
  }
  function hint(text) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = text;
    return p;
  }
  function divider() {
    const hr = document.createElement("hr");
    hr.className = "divider";
    return hr;
  }

  // src/component-patterns/view-options.ts
  function connectorSample(counted) {
    const sample = document.createElement("span");
    sample.className = "sample";
    sample.setAttribute("aria-hidden", "true");
    const start = document.createElement("span");
    start.className = "sample-endpoint";
    const line = document.createElement("span");
    line.className = "sample-connector";
    sample.append(start, line);
    const end = document.createElement("span");
    if (counted) {
      end.className = "sample-badge";
      end.textContent = "3";
    } else end.className = "sample-endpoint";
    sample.append(end);
    return sample;
  }
  function strokeSample(dashed) {
    const sample = document.createElement("span");
    sample.className = "stroke-sample";
    sample.dataset.dashed = String(dashed);
    sample.setAttribute("aria-hidden", "true");
    return sample;
  }
  function strokeStack() {
    const stack = document.createElement("span");
    stack.className = "stroke-stack";
    stack.setAttribute("aria-hidden", "true");
    stack.append(strokeSample(false), strokeSample(true));
    return stack;
  }
  function viewOptionsMenu(model, current, apply, reset) {
    let page = "root";
    const marks = marksOf(model);
    const panel2 = document.createElement("section");
    panel2.className = "panel settings";
    panel2.id = "explorer-view-options";
    panel2.setAttribute("aria-label", "View options");
    panel2.hidden = true;
    const trigger = iconButton("menu", "View options", () => panel2.hidden ? open() : close());
    trigger.classList.add("menu-trigger");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", panel2.id);
    const dot = document.createElement("span");
    dot.className = "active-dot";
    dot.hidden = true;
    trigger.append(dot);
    const orderingFrame = model.entities.find((e) => e.id === model.orderingFrameId);
    const orderingOptions2 = model.entities.filter(
      (e) => e.kind === "option" && !!orderingFrame && e.id.startsWith(`option:${orderingFrame.sourceId}:`)
    );
    const otherFrames = model.entities.filter((e) => (e.kind === "frame" || e.kind === "factor") && e.id !== model.orderingFrameId);
    const kinds = relationKinds(model);
    const toggleIn = (key, value) => {
      const set = new Set(current()[key]);
      if (set.has(value)) set.delete(value);
      else set.add(value);
      apply({ [key]: [...set] });
    };
    const chips = (items) => {
      const group = document.createElement("div");
      group.className = "chips";
      group.append(...items);
      return group;
    };
    const heading = (title, action) => {
      const head = document.createElement("div");
      head.className = "settings-head";
      if (page !== "root") {
        const back = iconButton("back", "Back to view options", () => {
          const origin = page;
          page = "root";
          render();
          panel2.querySelector(`[data-page="${origin}"]`)?.focus();
        });
        back.classList.add("back");
        head.append(back);
      }
      const strong = document.createElement("strong");
      strong.textContent = title;
      head.append(strong);
      if (action) head.append(action);
      return head;
    };
    const clearAction = (label, enabled, action) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "muted";
      button.textContent = label;
      button.disabled = !enabled;
      button.addEventListener("click", action);
      return button;
    };
    const pageRow = (label, detail, target, glyph) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "disclosure";
      button.dataset.page = target;
      if (glyph) button.append(icon(glyph));
      const text = document.createElement("span");
      text.textContent = label;
      const small = document.createElement("small");
      small.textContent = detail;
      button.append(text, small, icon("chevron"));
      button.addEventListener("click", () => {
        page = target;
        render();
        panel2.querySelector(".back")?.focus();
      });
      return button;
    };
    function render() {
      const options = current();
      dot.hidden = !(options.frames.length || options.emphasis.length);
      panel2.replaceChildren();
      if (page === "frames") {
        panel2.append(
          heading(
            "Dimensions",
            clearAction("Clear", options.frames.length > 0, () => apply({ frames: [] }))
          )
        );
        if (orderingFrame)
          panel2.append(
            field(
              orderingFrame.label,
              chips(
                orderingOptions2.map(
                  (option) => chip(
                    option.id,
                    option.label,
                    options.frames.includes(option.id),
                    marks.value(orderingFrame.id, option.sourceId),
                    () => toggleIn("frames", option.id)
                  )
                )
              ),
              markIcon(marks.frame(orderingFrame.sourceId))
            )
          );
        const frames = otherFrames.filter((e) => e.kind === "frame");
        const factors = otherFrames.filter((e) => e.kind === "factor");
        for (const [label, items] of [
          ["Referenced frames", frames],
          ["Referenced factors", factors]
        ])
          if (items.length)
            panel2.append(
              field(
                label,
                chips(
                  items.map(
                    (frame) => chip(
                      frame.id,
                      frame.label,
                      options.frames.includes(frame.id),
                      marks.frame(frame.sourceId, frame.kind),
                      () => toggleIn("frames", frame.id)
                    )
                  )
                )
              )
            );
        panel2.append(hint("Any selected value in each group."));
        return;
      }
      if (page === "emphasis") {
        panel2.append(
          heading(
            "Emphasize connections",
            clearAction("Reset emphasis", options.emphasis.length > 0, () => apply({ emphasis: [] }))
          ),
          hint("Choose one or more types. Other connections stay visible."),
          chips(
            kinds.map((kind) => {
              const count = model.connections.filter((c) => c.kind === kind.id).length;
              return chip(
                kind.id,
                `${relationKindCopy(kind.id, kinds)} (${count})`,
                options.emphasis.includes(kind.id),
                null,
                () => toggleIn("emphasis", kind.id)
              );
            })
          )
        );
        return;
      }
      panel2.append(heading("View options"));
      if (aViewGroupsItsElements(options.view))
        panel2.append(
          field(
            "Group elements",
            segmented(
              "Group elements",
              [
                { value: "grouped", label: orderingFrame?.label ?? "Ordering" },
                { value: "none", label: "None" }
              ],
              options.group ? "grouped" : "none",
              (value) => apply({ group: value === "grouped" })
            )
          )
        );
      if (options.view === "frames") panel2.append(hint("Frame choices and connections apply to the artifact views."));
      else {
        panel2.append(
          pageRow("Dimensions", options.frames.length ? `${options.frames.length} selected` : "All cards", "frames", "filter"),
          divider(),
          field(
            "Connections",
            segmented(
              "Connections",
              [
                { value: "", label: "Off" },
                { value: "relations", label: "Relations" },
                { value: "composition", label: "Composition" }
              ],
              options.connections,
              (value) => apply({ connections: value })
            )
          )
        );
        if (options.connections === "relations")
          panel2.append(pageRow("Emphasize", options.emphasis.length ? `${options.emphasis.length} selected` : "No emphasis", "emphasis"));
        if (options.connections)
          panel2.append(
            field(
              "Display",
              segmented(
                "Display",
                [
                  { value: "lines", label: "Lines", content: () => connectorSample(false) },
                  { value: "counts", label: "Counts", content: () => connectorSample(true) }
                ],
                options.display,
                (value) => apply({ display: value })
              )
            )
          );
        if (options.connections === "composition" && options.display === "lines")
          panel2.append(
            field(
              "Composition lines",
              segmented(
                "Composition lines",
                [
                  {
                    value: "uniform",
                    label: "Required",
                    tooltip: "Hide situational connections",
                    content: () => strokeSample(false)
                  },
                  {
                    value: "distinct",
                    label: "Required / optional",
                    tooltip: "Show all connections",
                    content: () => strokeStack()
                  }
                ],
                options.lineStyle,
                (value) => apply({ lineStyle: value })
              )
            )
          );
      }
      const resetRow = labelledButton("reset", "Reset view options", reset);
      resetRow.classList.add("disclosure");
      resetRow.dataset.action = "reset";
      panel2.append(divider(), resetRow);
    }
    function open() {
      page = "root";
      render();
      panel2.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
    }
    function close(focusTrigger = false) {
      panel2.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      if (focusTrigger) trigger.focus();
    }
    panel2.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      if (page !== "root") {
        const origin = page;
        page = "root";
        render();
        panel2.querySelector(`[data-page="${origin}"]`)?.focus();
      } else close(true);
    });
    return { trigger, panel: panel2, render, open, close, isOpen: () => !panel2.hidden };
  }

  // src/component-patterns/search-panel.ts
  function searchPanel(model, pick, close) {
    const surface = panel("search", "Find an artifact or element", close);
    surface.title.textContent = "Find an artifact or element";
    const input = document.createElement("input");
    input.type = "search";
    input.setAttribute("aria-label", "Search names, aliases or questions");
    input.placeholder = "Search names, aliases or questions";
    const results = document.createElement("div");
    results.setAttribute("aria-live", "polite");
    surface.body.append(input, results);
    const candidates = model.entities.filter((e) => e.kind === "artifact" || e.kind === "element");
    const render = () => {
      const query = input.value.trim().toLowerCase();
      const matches = candidates.filter((e) => `${e.label} ${e.description} ${JSON.stringify(e.raw)}`.toLowerCase().includes(query));
      results.replaceChildren();
      if (!matches.length) {
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "No matches";
        results.append(empty);
        return;
      }
      results.append(
        disclosureList(
          matches.map((entity) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "result";
            button.dataset.result = entity.id;
            const kind = document.createElement("span");
            kind.className = "muted";
            kind.textContent = human(entity.kind);
            const label = document.createElement("strong");
            label.textContent = entity.label;
            const detail = document.createElement("span");
            detail.className = "muted";
            detail.textContent = entity.description || String(entity.raw.enablement?.action ?? "");
            button.append(kind, label, detail);
            button.addEventListener("click", () => pick(entity.id));
            return button;
          }),
          RESULT_LIMIT
        )
      );
    };
    input.addEventListener("input", render);
    render();
    return surface.root;
  }

  // src/component-patterns/minimap.ts
  var SVG5 = "http://www.w3.org/2000/svg";
  function minimap(scene, navigate, jumpTo, close) {
    const root = document.createElement("aside");
    root.className = "panel minimap";
    root.setAttribute("aria-label", "Map overview");
    const head = document.createElement("div");
    head.className = "minimap-head";
    head.title = "Drag to move the minimap";
    const title = document.createElement("strong");
    title.textContent = "Map";
    const closeButton = iconButton("close", "Close map overview", close);
    closeButton.classList.add("close");
    head.append(title, closeButton);
    const plot = document.createElementNS(SVG5, "svg");
    plot.classList.add("plot");
    const pad = tokenNumber("--kb-scene-margin");
    const box = { x: scene.bounds.x - pad, y: scene.bounds.y - pad, w: scene.bounds.w + pad * 2, h: scene.bounds.h + pad * 2 };
    plot.setAttribute("viewBox", `${box.x} ${box.y} ${box.w} ${box.h}`);
    plot.setAttribute("preserveAspectRatio", "none");
    plot.setAttribute("role", "img");
    plot.setAttribute("aria-label", "Map overview; drag to move the view");
    for (const card of scene.layout.cards) {
      const rect = document.createElementNS(SVG5, "rect");
      rect.setAttribute("x", String(card.x));
      rect.setAttribute("y", String(card.y));
      rect.setAttribute("width", String(card.w));
      rect.setAttribute("height", String(card.h));
      rect.dataset.kind = card.kind;
      plot.append(rect);
    }
    const view = document.createElementNS(SVG5, "rect");
    view.dataset.camera = "true";
    plot.append(view);
    const hintText = document.createElement("p");
    hintText.className = "minimap-hint";
    hintText.textContent = "Click or drag to move the view";
    root.append(head, plot, hintText);
    let plotDrag = null;
    const scaleOf = () => {
      const rect = plot.getBoundingClientRect();
      return { x: box.w / rect.width, y: box.h / rect.height, rect };
    };
    plot.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      event.stopPropagation();
      plot.setPointerCapture(event.pointerId);
      plotDrag = { x: event.clientX, y: event.clientY };
    });
    plot.addEventListener("pointermove", (event) => {
      if (!plotDrag) return;
      event.stopPropagation();
      const scale = scaleOf();
      navigate({ x: (event.clientX - plotDrag.x) * scale.x, y: (event.clientY - plotDrag.y) * scale.y });
      plotDrag = { x: event.clientX, y: event.clientY };
    });
    plot.addEventListener("click", (event) => {
      event.stopPropagation();
      const scale = scaleOf();
      jumpTo({ x: box.x + (event.clientX - scale.rect.left) * scale.x, y: box.y + (event.clientY - scale.rect.top) * scale.y });
    });
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"])
      plot.addEventListener(type, () => {
        plotDrag = null;
      });
    let move = null;
    const clearance = tokenNumber("--kb-minimap-clearance");
    const place = (left, top) => {
      const parent = root.offsetParent;
      if (!parent) return;
      root.style.left = `${Math.max(clearance, Math.min(left, parent.clientWidth - root.offsetWidth - clearance))}px`;
      root.style.top = `${Math.max(clearance, Math.min(top, parent.clientHeight - root.offsetHeight - clearance))}px`;
      root.style.right = "auto";
      root.style.bottom = "auto";
    };
    head.addEventListener("pointerdown", (event) => {
      if (event.target.closest("button") || event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      move = { x: event.clientX, y: event.clientY, left: root.offsetLeft, top: root.offsetTop };
      head.setPointerCapture(event.pointerId);
      root.dataset.dragging = "true";
    });
    head.addEventListener("pointermove", (event) => {
      if (!move) return;
      event.stopPropagation();
      place(move.left + event.clientX - move.x, move.top + event.clientY - move.y);
    });
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"])
      head.addEventListener(type, () => {
        move = null;
        delete root.dataset.dragging;
      });
    return {
      root,
      update(camera, viewport) {
        view.setAttribute("x", String(-camera.x / camera.z));
        view.setAttribute("y", String(-camera.y / camera.z));
        view.setAttribute("width", String(viewport.width / camera.z));
        view.setAttribute("height", String(viewport.height / camera.z));
      },
      keepWithin() {
        if (root.style.left) place(root.offsetLeft, root.offsetTop);
      }
    };
  }

  // src/component-patterns/universe-viewer.ts
  var OPENING_ORIGIN = 30;
  var VIEW_ORIGIN = 25;
  var OPENING_ZOOM = 0.8;
  var FRAMES_ZOOM = 0.85;
  var CONTENT_ZOOM = 0.7;
  var DRAG_THRESHOLD = 4;
  var DISMISS_THRESHOLD = 5;
  var WHEEL_ZOOM_RATE = 5e-3;
  var STEP_ZOOM = tokenNumber("--kb-zoom-step");
  function measurer() {
    const context = document.createElement("canvas").getContext("2d");
    if (!context) return approximateText;
    const cache = /* @__PURE__ */ new Map();
    return (text, size) => {
      const key = `${size}|${text}`;
      const known = cache.get(key);
      if (known !== void 0) return known;
      context.font = `${size}px ${getComputedStyle(document.body).fontFamily || "sans-serif"}`;
      const width = context.measureText(text).width;
      cache.set(key, width);
      return width;
    };
  }
  function browserSampler(container) {
    const SVG6 = "http://www.w3.org/2000/svg";
    return (d, count) => {
      const path = document.createElementNS(SVG6, "path");
      path.setAttribute("d", d);
      container.append(path);
      const length = path.getTotalLength();
      const samples = Array.from({ length: count }, (_, i) => {
        const point = path.getPointAtLength(length * (i + 1) / (count + 1));
        return { x: point.x, y: point.y };
      });
      const middle = path.getPointAtLength(length / 2);
      path.remove();
      return { samples, middle: { x: middle.x, y: middle.y } };
    };
  }
  function mountUniverseViewer(host2, input, viewerOptions = {}) {
    const model = validateModel(input);
    const controller = new AbortController();
    const signal = controller.signal;
    const shadow = host2.shadowRoot ?? host2.attachShadow({ mode: "open" });
    shadow.replaceChildren();
    const style = document.createElement("style");
    style.textContent = tokens_default + patterns_default;
    const shell = document.createElement("div");
    shell.className = "shell";
    shell.tabIndex = -1;
    shadow.append(style, shell);
    const measure = measurer();
    let options = updateOptions(initialOptions(viewerOptions.initial?.view), viewerOptions.initial ?? {});
    let selection = emptySelection();
    let camera = { x: 0, y: 0, z: 1 };
    let insets = noInsets();
    let destroyed = false;
    let animation = 0;
    let scene;
    let map = null;
    const mapBounds = () => map?.drawnBounds() ?? scene.bounds;
    const hovered = showAfterTheLastOfferRests("", tokenNumber("--kb-motion-dwell"), (id) => map?.highlight(selection, id));
    let detail = null;
    let search = null;
    let overview = null;
    let share = null;
    let overviewMap = null;
    let legendBox = null;
    const reducedMotion = () => !!globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const viewportSize = () => ({ width: viewport.clientWidth, height: viewport.clientHeight });
    const narrow = () => viewport.clientWidth < tokenNumber("--kb-size-narrow-threshold");
    const bar = topBar(model, {
      openOverview: () => toggleOverview(),
      setView: (view) => setViewOptions({ view }),
      toggleTheme: () => setViewOptions({ theme: effectiveTheme() === "light" ? "dark" : "light" }),
      toggleShare: () => toggleShare()
    });
    const menu = viewOptionsMenu(
      model,
      () => options,
      (patch) => setViewOptions(patch),
      () => resetViewOptions()
    );
    bar.utilities.append(menu.trigger);
    const viewport = document.createElement("div");
    viewport.className = "viewport";
    viewport.setAttribute("aria-label", "Universe map");
    const bottom = dock({
      search: () => search ? closeSearch() : openSearch(),
      toggleMinimap: () => overviewMap ? closeMinimap() : openMinimap(),
      fit: () => fit(),
      zoomIn: () => stepZoom(STEP_ZOOM),
      zoomOut: () => stepZoom(1 / STEP_ZOOM),
      actualSize: () => stepZoom(1 / camera.z)
    });
    shell.append(bar.root, viewport, bottom.root, menu.panel);
    const effectiveTheme = () => {
      if (options.theme !== "auto") return options.theme;
      return globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };
    const chromeTop = () => bar.root.offsetHeight;
    const chromeBottom = () => bottom.root.offsetHeight + tokenNumber("--kb-space-4") * 2;
    function applyCamera(next) {
      camera = constrainCamera({ ...next, z: clampZoom(next.z) }, mapBounds(), viewportSize(), insets);
      map?.applyCamera(camera);
      bottom.setZoom(camera.z);
      overviewMap?.update(camera, viewportSize());
    }
    function stopMotion() {
      if (animation) cancelAnimationFrame(animation);
      animation = 0;
    }
    function animateTo(target) {
      stopMotion();
      const goal = constrainCamera({ ...target, z: clampZoom(target.z) }, mapBounds(), viewportSize(), insets);
      if (reducedMotion()) {
        applyCamera(goal);
        return;
      }
      const from = { ...camera };
      const started = performance.now();
      const duration = motionDuration();
      const step = (now) => {
        const fraction = Math.min(1, (now - started) / duration);
        applyCamera(interpolate(from, goal, fraction));
        animation = fraction < 1 ? requestAnimationFrame(step) : 0;
      };
      animation = requestAnimationFrame(step);
    }
    function rebuild(keepCamera = false) {
      const previous = { ...camera };
      const hadFocus = shadow.activeElement;
      const probe = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      probe.style.position = "absolute";
      probe.style.opacity = "0";
      viewport.append(probe);
      scene = buildScene(model, options, selection, camera.z, browserSampler(probe));
      probe.remove();
      map = universeMap(
        scene,
        model,
        {
          selectEntity: (id) => select(id),
          selectConnection: (path) => selectConnection(path),
          hover: (id) => hovered.offer(id)
        },
        measure
      );
      map.highlight(selection, hovered.shown());
      viewport.replaceChildren(map.root);
      if (!scene.layout.cards.length) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No cards match the current view options.";
        viewport.append(empty);
      }
      shell.dataset.theme = options.theme === "auto" ? "" : options.theme;
      bar.renderTabs(options.view);
      bar.syncTheme(effectiveTheme());
      menu.render();
      legendBox?.remove();
      legendBox = null;
      const rows = legendRows(scene);
      if (rows.length) {
        legendBox = legend(rows);
        shell.append(legendBox);
      }
      if (overviewMap) {
        const position = { left: overviewMap.root.style.left, top: overviewMap.root.style.top };
        overviewMap.root.remove();
        overviewMap = null;
        openMinimap(position.left ? position : void 0);
      }
      applyCamera(keepCamera ? previous : camera);
      if (hadFocus && !shadow.contains(shadow.activeElement)) shell.focus({ preventScroll: true });
    }
    const subjectExists = (id) => scene.layout.cards.some((c) => c.id === id) || scene.layout.boundaries.some((b) => b.id === id) || model.rules.some((r) => r.id === id);
    function computeInsets() {
      if (!detail) return noInsets();
      const width = detail.offsetWidth + tokenNumber("--kb-overlay-clearance") * 2;
      const height = detail.offsetHeight + tokenNumber("--kb-overlay-clearance") * 2;
      return narrow() ? { left: 0, right: 0, top: chromeTop() + height, bottom: chromeBottom() } : { left: width, right: 0, top: chromeTop(), bottom: chromeBottom() };
    }
    function panelTopAlongside(subjectCentre, height) {
      const clearance = tokenNumber("--kb-overlay-clearance");
      const first = viewport.offsetTop + clearance;
      const last = viewport.offsetTop + viewport.clientHeight - chromeBottom() - height;
      return Math.max(first, Math.min(Math.max(first, last), viewport.offsetTop + subjectCentre - height / 2));
    }
    function placeDetail(against = camera) {
      if (!detail) return;
      insets = computeInsets();
      const bounds = narrow() ? null : subjectBounds(scene, selection);
      const top = bounds ? panelTopAlongside((bounds.y + bounds.h / 2) * against.z + against.y, detail.offsetHeight) : viewport.offsetTop + tokenNumber("--kb-overlay-clearance");
      detail.style.top = `${top}px`;
    }
    function closeDetail() {
      detail?.remove();
      detail = null;
      insets = noInsets();
    }
    function openDetail(node) {
      closeDetail();
      detail = node;
      shell.append(detail);
      placeDetail();
    }
    function frameSelection() {
      const bounds = selectionBounds(scene, selection);
      if (!bounds) return;
      const target = frameCamera(bounds, viewportSize(), insets);
      if (!target) return;
      const goal = constrainCamera({ ...target, z: clampZoom(target.z) }, mapBounds(), viewportSize(), insets);
      placeDetail(goal);
      animateTo(goal);
    }
    function clearSelection(refit = true) {
      selection = emptySelection();
      hovered.showNow("");
      closeDetail();
      closeShare();
      rebuild(true);
      if (refit) fit();
    }
    function dismissDetail() {
      if (!detail) return false;
      closeDetail();
      closeShare();
      fit();
      return true;
    }
    function select(subject) {
      if (destroyed) return;
      menu.close();
      closeShare();
      if (!subject) {
        clearSelection();
        return;
      }
      const entity = model.entities.find((e) => e.id === subject);
      if (entity && !subjectExists(subject)) {
        const view = entity.kind === "element" ? "elements" : entity.kind === "artifact" ? options.view === "frames" ? "artifacts" : options.view : "frames";
        options = updateOptions(options, { view, frames: [] });
        selection = emptySelection();
        rebuild();
      }
      if (!subjectExists(subject)) return;
      closeSearch();
      selection = { entity: subject, connection: "", option: subject.startsWith("option:") ? subject : "" };
      rebuild(true);
      openDetail(
        detailOverlay(
          model,
          subject,
          () => dismissDetail(),
          (id) => select(id)
        ).root
      );
      frameSelection();
    }
    function selectConnection(path) {
      if (destroyed) return;
      menu.close();
      if (!path || selection.connection === path) {
        clearSelection();
        return;
      }
      const nub = path.startsWith("nub:");
      const id = nub ? path.slice(4) : "";
      const edge = nub ? {
        path,
        from: id,
        to: id,
        label: "Connections",
        ordered: false,
        nub: true,
        sources: scene.edges.filter((e) => e.from === id || e.to === id || e.targetPair?.includes(id)).flatMap((e) => e.sources ?? [{ source: e, composition: [] }])
      } : scene.edges.find((e) => e.path === path);
      if (!edge) return;
      selection = { entity: "", connection: path, option: "" };
      closeSearch();
      rebuild(true);
      openDetail(
        connectionOverlay(
          model,
          edge,
          () => dismissDetail(),
          (target) => select(target)
        )
      );
      frameSelection();
    }
    function setViewOptions(patch) {
      if (destroyed) return;
      const next = updateOptions(options, patch);
      const viewChanged = next.view !== options.view;
      options = next;
      if (viewChanged) {
        selection = emptySelection();
        closeDetail();
        rebuild();
        applyCamera(openingCamera(options.view));
        return;
      }
      rebuild(true);
      if (selection.entity)
        openDetail(
          detailOverlay(
            model,
            selection.entity,
            () => dismissDetail(),
            (id) => select(id)
          ).root
        );
      menu.render();
    }
    function resetViewOptions() {
      const saved = { ...camera };
      const keep = selection;
      options = updateOptions(initialOptions(options.view), { ...viewerOptions.initial, view: options.view });
      selection = keep;
      rebuild(true);
      applyCamera(saved);
      if (selection.entity)
        openDetail(
          detailOverlay(
            model,
            selection.entity,
            () => dismissDetail(),
            (id) => select(id)
          ).root
        );
      menu.render();
    }
    function fit() {
      animateTo(fitCameraWithin(mapBounds(), viewportSize(), insets));
    }
    function openingCamera(view, first = false) {
      const origin = first ? OPENING_ORIGIN : VIEW_ORIGIN;
      return { x: origin, y: origin, z: first ? OPENING_ZOOM : view === "frames" ? FRAMES_ZOOM : CONTENT_ZOOM };
    }
    function stepZoom(factor) {
      animateTo(zoomAround(camera, camera.z * factor, viewport.clientWidth / 2, viewport.clientHeight / 2));
    }
    function openSearch() {
      menu.close();
      closeSearch();
      search = searchPanel(
        model,
        (id) => select(id),
        () => closeSearch()
      );
      shell.append(search);
      search.style.top = `${viewport.offsetTop + tokenNumber("--kb-overlay-clearance")}px`;
      search.querySelector("input")?.focus();
    }
    function closeSearch() {
      search?.remove();
      search = null;
    }
    function openMinimap(position) {
      overviewMap = minimap(
        scene,
        (delta) => applyCamera({ ...camera, x: camera.x - delta.x * camera.z, y: camera.y - delta.y * camera.z }),
        (point) => applyCamera({ ...camera, x: viewport.clientWidth / 2 - point.x * camera.z, y: viewport.clientHeight / 2 - point.y * camera.z }),
        () => closeMinimap()
      );
      if (position) Object.assign(overviewMap.root.style, position, { right: "auto", bottom: "auto" });
      shell.append(overviewMap.root);
      overviewMap.update(camera, viewportSize());
      bottom.setMinimapOpen(true);
    }
    function closeMinimap() {
      overviewMap?.root.remove();
      overviewMap = null;
      bottom.setMinimapOpen(false);
    }
    function toggleOverview() {
      if (overview) {
        overview.scrim.remove();
        overview.root.remove();
        overview = null;
        return;
      }
      overview = universeOverview(model, () => toggleOverview());
      shell.append(overview.scrim, overview.root);
    }
    function toggleShare() {
      if (share) {
        closeShare();
        return;
      }
      share = shareMenu(() => void download());
      bar.utilities.append(share);
      bar.shareButton.setAttribute("aria-expanded", "true");
    }
    function closeShare() {
      share?.remove();
      share = null;
      bar.shareButton.setAttribute("aria-expanded", "false");
    }
    async function exportSvg(exportOptions = {}) {
      await document.fonts?.ready;
      const probe = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      probe.style.position = "absolute";
      probe.style.opacity = "0";
      viewport.append(probe);
      const clean = buildScene(model, options, emptySelection(), 1, browserSampler(probe));
      probe.remove();
      return serializeSvg(clean, model, exportOptions.theme ?? "auto", measure);
    }
    async function download() {
      const svg = await exportSvg();
      const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${model.universe.id}-map.svg`;
      anchor.click();
      URL.revokeObjectURL(url);
      closeShare();
    }
    const pointers = /* @__PURE__ */ new Map();
    let press = null;
    let pinch = null;
    const local = (event) => {
      const box = viewport.getBoundingClientRect();
      return { x: event.clientX - box.left, y: event.clientY - box.top };
    };
    viewport.addEventListener(
      "pointerdown",
      (event) => {
        if (event.target.closest("button,[role=button],.panel")) return;
        stopMotion();
        viewport.setPointerCapture(event.pointerId);
        pointers.set(event.pointerId, local(event));
        if (pointers.size === 2) {
          const [a, b] = [...pointers.values()];
          pinch = { distance: Math.hypot(a.x - b.x, a.y - b.y), camera: { ...camera } };
          press = null;
        } else {
          const point = local(event);
          press = { x: point.x, y: point.y, moved: false, camera: { ...camera } };
        }
      },
      { signal }
    );
    viewport.addEventListener(
      "pointermove",
      (event) => {
        if (!pointers.has(event.pointerId)) return;
        pointers.set(event.pointerId, local(event));
        if (pinch && pointers.size === 2) {
          const [a, b] = [...pointers.values()];
          const distance = Math.hypot(a.x - b.x, a.y - b.y);
          applyCamera(zoomAround(pinch.camera, pinch.camera.z * distance / pinch.distance, (a.x + b.x) / 2, (a.y + b.y) / 2));
          return;
        }
        if (!press) return;
        const point = local(event);
        const dx = point.x - press.x;
        const dy = point.y - press.y;
        if (!press.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
        press.moved = true;
        applyCamera({ z: press.camera.z, x: press.camera.x + dx, y: press.camera.y + dy });
      },
      { signal }
    );
    const release = (event) => {
      pointers.delete(event.pointerId);
      if (pointers.size < 2) pinch = null;
      if (!press) return;
      const point = local(event);
      const still = Math.hypot(point.x - press.x, point.y - press.y) < DISMISS_THRESHOLD;
      const blank = !event.target.closest("button,[role=button],.panel");
      if (still && blank && event.type === "pointerup" && (selection.entity || selection.connection)) clearSelection();
      press = null;
    };
    viewport.addEventListener("pointerup", release, { signal });
    viewport.addEventListener("pointercancel", release, { signal });
    viewport.addEventListener(
      "dblclick",
      (event) => {
        if (event.target.closest("button,[role=button],.panel")) return;
        event.preventDefault();
        fit();
      },
      { signal }
    );
    viewport.addEventListener(
      "wheel",
      (event) => {
        if (event.target.closest(".panel")) return;
        event.preventDefault();
        stopMotion();
        const box = viewport.getBoundingClientRect();
        if (event.ctrlKey || event.metaKey)
          applyCamera(
            zoomAround(camera, camera.z * Math.exp(-event.deltaY * WHEEL_ZOOM_RATE), event.clientX - box.left, event.clientY - box.top)
          );
        else applyCamera({ ...camera, x: camera.x - event.deltaX, y: camera.y - event.deltaY });
      },
      { passive: false, signal }
    );
    shell.addEventListener(
      "pointerdown",
      (event) => {
        const target = event.target;
        if (menu.isOpen() && !menu.panel.contains(target) && !menu.trigger.contains(target)) menu.close();
        if (share && !share.contains(target) && !bar.shareButton.contains(target)) closeShare();
      },
      { capture: true, signal }
    );
    shell.addEventListener(
      "keydown",
      (event) => {
        if (event.key !== "Escape") return;
        if (menu.isOpen()) menu.close(true);
        else if (share) closeShare();
        else if (overview) toggleOverview();
        else if (search) closeSearch();
        else if (!dismissDetail()) return;
        else return;
        event.preventDefault();
      },
      { signal }
    );
    const resize = new ResizeObserver(() => {
      if (destroyed) return;
      placeDetail();
      applyCamera(camera);
      overviewMap?.keepWithin();
    });
    resize.observe(viewport);
    const scheme = globalThis.matchMedia?.("(prefers-color-scheme: dark)");
    scheme?.addEventListener("change", () => bar.syncTheme(effectiveTheme()), { signal });
    scene = buildScene(model, options, selection, 1);
    rebuild();
    applyCamera(openingCamera(options.view, true));
    document.fonts?.ready.then(() => {
      if (destroyed) return;
      rebuild(true);
      if (selection.entity || selection.connection) frameSelection();
      else applyCamera(camera);
    });
    return {
      getState: () => ({
        options: { ...options, emphasis: [...options.emphasis], frames: [...options.frames] },
        selection: { ...selection },
        camera: { ...camera }
      }),
      setViewOptions,
      select,
      selectConnection,
      fit,
      exportSvg,
      destroy() {
        if (destroyed) return;
        destroyed = true;
        stopMotion();
        hovered.showNow("");
        controller.abort();
        resize.disconnect();
        shadow.replaceChildren();
      }
    };
  }

  // src/lib/embed.ts
  function parseEmbedded(text) {
    return JSON.parse(text);
  }

  // src/standalone.ts
  var host = document.getElementById("explorer");
  var data = document.getElementById("explorer-model");
  if (host && data) {
    try {
      host.explorerViewer = mountUniverseViewer(host, parseEmbedded(data.textContent ?? ""));
    } catch (error) {
      host.textContent = `This file's embedded universe model cannot be shown: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
})();
