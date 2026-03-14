/**
 * Bin Buddy Character Animation
 *
 * Plays frame-by-frame PNG animations as a pop-up overlay.
 *
 * Usage:
 *   playBuddyAnimation('happy');                         // defaults
 *   playBuddyAnimation('sad', { size: 300, fps: 30 });  // custom
 *   preloadBuddyFrames('happy');                         // warm cache
 */

(function () {
  // Frame counts for each animation type
  var FRAME_COUNTS = { happy: 121, sad: 122 };

  // Cache: { happy: [Image, ...], sad: [Image, ...] }
  var frameCache = {};

  // Currently running animation state
  var activeTimer = null;
  var activeOverlay = null;

  // Whether CSS has been injected
  var cssInjected = false;

  // Inject CSS styles once
  function injectCSS() {
    if (cssInjected) return;
    cssInjected = true;
    var style = document.createElement('style');
    style.textContent =
      '.buddy-overlay {' +
        'position: fixed;' +
        'z-index: 10000;' +
        'pointer-events: none;' +
      '}' +
      '.buddy-overlay img {' +
        'width: 100%;' +
        'height: 100%;' +
        'object-fit: contain;' +
      '}' +
      // Pop-in: scale from 0 to 1 with a slight bounce
      '.buddy-pop-in {' +
        'animation: buddyPopIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;' +
      '}' +
      '@keyframes buddyPopIn {' +
        '0%   { transform: scale(0); opacity: 0; }' +
        '70%  { transform: scale(1.1); opacity: 1; }' +
        '100% { transform: scale(1); opacity: 1; }' +
      '}' +
      // Fade-out: shrink and disappear
      '.buddy-fade-out {' +
        'animation: buddyFadeOut 0.4s ease-out forwards;' +
      '}' +
      '@keyframes buddyFadeOut {' +
        '0%   { opacity: 1; transform: scale(1); }' +
        '100% { opacity: 0; transform: scale(0.8); }' +
      '}';
    document.head.appendChild(style);
  }

  /**
   * Preload all frames for a given animation type.
   * Returns a promise that resolves with the Image array.
   *
   * @param {string} type - 'happy' or 'sad'
   * @returns {Promise<HTMLImageElement[]>}
   */
  function preloadBuddyFrames(type) {
    // Return cached frames if already loaded
    if (frameCache[type]) {
      return Promise.resolve(frameCache[type]);
    }

    var count = FRAME_COUNTS[type];
    if (!count) {
      return Promise.reject(new Error('Unknown animation type: ' + type));
    }

    var frames = [];
    var promises = [];

    for (var i = 1; i <= count; i++) {
      var img = new Image();
      // Pad frame number to 3 digits: frame_001.png, frame_002.png, ...
      var num = String(i).padStart(3, '0');
      img.src = '/asset/' + type + '/frame_' + num + '.png';
      frames.push(img);
      promises.push(
        new Promise(function (resolve, reject) {
          var image = img;
          image.onload = resolve;
          image.onerror = function () {
            resolve(); // don't block on missing frames
          };
        })
      );
    }

    return Promise.all(promises).then(function () {
      frameCache[type] = frames;
      return frames;
    });
  }

  /**
   * Play the Bin Buddy character animation.
   *
   * @param {string}  type             - 'happy' or 'sad'
   * @param {Object}  [opts]           - Optional configuration
   * @param {number}  [opts.size=200]  - Width/height in pixels
   * @param {number}  [opts.fps=24]    - Frames per second
   * @param {string}  [opts.position='center'] - 'center', 'bottom-right', or 'bottom-left'
   * @param {number}  [opts.fadeOutMs=400]     - Fade-out duration in ms
   * @param {boolean} [opts.loop=false]        - Loop animation until dismissBuddyAnimation() is called
   */
  function playBuddyAnimation(type, opts) {
    opts = opts || {};
    var size = opts.size || 350;
    var fps = opts.fps || 24;
    var position = opts.position || 'center';
    var fadeOutMs = opts.fadeOutMs || 400;
    var loop = opts.loop || false;

    injectCSS();

    // Clear any currently running animation
    if (activeTimer) {
      clearInterval(activeTimer);
      activeTimer = null;
    }
    if (activeOverlay && activeOverlay.parentNode) {
      activeOverlay.parentNode.removeChild(activeOverlay);
      activeOverlay = null;
    }

    // Preload frames then start playback
    preloadBuddyFrames(type).then(function (frames) {
      if (!frames || frames.length === 0) return;

      // Create overlay container
      var overlay = document.createElement('div');
      overlay.className = 'buddy-overlay buddy-pop-in';
      overlay.style.width = size + 'px';
      overlay.style.height = size + 'px';

      // Position the overlay
      if (position === 'bottom-right') {
        overlay.style.bottom = '20px';
        overlay.style.right = '20px';
      } else if (position === 'bottom-left') {
        overlay.style.bottom = '20px';
        overlay.style.left = '20px';
      } else {
        // center
        overlay.style.top = '50%';
        overlay.style.left = '50%';
        overlay.style.marginTop = '-' + (size / 2) + 'px';
        overlay.style.marginLeft = '-' + (size / 2) + 'px';
      }

      // Create the image element that will display each frame
      var img = document.createElement('img');
      img.src = frames[0].src;
      img.alt = type + ' character';
      overlay.appendChild(img);
      document.body.appendChild(overlay);
      activeOverlay = overlay;

      // Play frames in sequence
      var frameIndex = 0;
      activeTimer = setInterval(function () {
        frameIndex++;
        if (frameIndex >= frames.length) {
          if (loop) {
            // Loop: restart from the first frame
            frameIndex = 0;
          } else {
            // Last frame reached — fade out and clean up
            clearInterval(activeTimer);
            activeTimer = null;
            overlay.classList.remove('buddy-pop-in');
            overlay.classList.add('buddy-fade-out');
            overlay.addEventListener('animationend', function () {
              if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
              }
              if (activeOverlay === overlay) {
                activeOverlay = null;
              }
            });
            return;
          }
        }
        img.src = frames[frameIndex].src;
      }, 1000 / fps);
    });
  }

  // Dismiss the currently playing animation with a fade-out
  function dismissBuddyAnimation() {
    if (activeTimer) {
      clearInterval(activeTimer);
      activeTimer = null;
    }
    if (activeOverlay) {
      var overlay = activeOverlay;
      overlay.classList.remove('buddy-pop-in');
      overlay.classList.add('buddy-fade-out');
      overlay.addEventListener('animationend', function () {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
        if (activeOverlay === overlay) {
          activeOverlay = null;
        }
      });
    }
  }

  // Expose functions globally
  window.playBuddyAnimation = playBuddyAnimation;
  window.dismissBuddyAnimation = dismissBuddyAnimation;
  window.preloadBuddyFrames = preloadBuddyFrames;
})();
