function initMap() {
    // Create a Leaflet map with a default location and zoom level
    var map = L.map('map').setView([51.505, -0.09], 13);

    // Add a tile layer (you may need to replace this with a suitable tile layer)
    L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.{ext}', {
        attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ext: 'png'
    }).addTo(map);
}

// Attach the callback function to the window object
window.initMap = initMap;
