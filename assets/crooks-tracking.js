/*
 * CROOKSLDN — order tracking.
 * Only job: pick which order record is on screen. Everything the page states
 * is rendered server-side from real order data, so with this file absent the
 * page still works — every record simply renders stacked.
 */
(function () {
  'use strict';

  function init(root) {
    var picks = root.querySelectorAll('[data-crk-track-pick]');
    var records = root.querySelectorAll('[data-crk-track-record]');
    if (!records.length) return;

    // Secondary records are marked in Liquid rather than hidden there, so a
    // no-JS visitor sees all of them instead of one.
    for (var i = 0; i < records.length; i++) {
      if (records[i].hasAttribute('data-crk-track-secondary')) records[i].hidden = true;
    }
    if (!picks.length) return;

    function show(name) {
      for (var r = 0; r < records.length; r++) {
        records[r].hidden = records[r].getAttribute('data-crk-track-record') !== name;
      }
      for (var p = 0; p < picks.length; p++) {
        picks[p].setAttribute('aria-pressed', picks[p].getAttribute('data-crk-track-pick') === name ? 'true' : 'false');
      }
    }
    for (var b = 0; b < picks.length; b++) {
      picks[b].addEventListener('click', function (e) {
        show(e.currentTarget.getAttribute('data-crk-track-pick'));
      });
    }
  }

  function mountAll(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    var nodes = root.querySelectorAll('[data-crk-section="tracking"]');
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i]._crkTrack) { nodes[i]._crkTrack = true; init(nodes[i]); }
    }
    if (root.matches && root.matches('[data-crk-section="tracking"]') && !root._crkTrack) {
      root._crkTrack = true; init(root);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else { mountAll(document); }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
