# TODO - Fix Cluster View

## Task: Fix cluster view performance and rendering issues

### Information Gathered:
- The app has ~10,000 coffee shop locations in Bandung
- There are two map views: Heatmap and Cluster
- The `create_cluster_map` function exists and uses MarkerCluster from folium.plugins
- The code imports MarkerCluster correctly
- The cluster view may be slow or not rendering properly due to:
  1. Adding popups to all 10,000 markers causes performance issues
  2. Large dataset causes slow rendering
  3. Need to optimize marker creation

### Plan:
1. Optimize the `create_cluster_map` function:
   - Remove popups from markers (they can be added on click via JavaScript callback)
   - Use lighter CircleMarker without popup content initially
   - Add options to customize cluster appearance
   - Reduce initial cluster radius for better performance

2. Add performance improvements:
   - Limit initial markers to a subset when no address is searched
   - Use chunked processing for large datasets

### Dependent Files:
- app.py - Main application file containing the cluster map function

### Followup steps:
- Test the cluster view with both small and large datasets
- Verify map renders correctly with clustering enabled
- Test toggle between Heatmap and Cluster views

### Status: Completed

## Changes Made:
1. Changed from `Marker` to `folium.CircleMarker` for better cluster rendering
2. Increased `disable_clustering_at_zoom` from 16 to 18 for better performance
3. Increased `max_cluster_radius` from 50 to 60 for smoother clustering
4. Increased marker radius from 4 to 5 with higher fillOpacity (0.8 vs 0.7) for better visibility
5. Added explicit `icon_create_function=None` and `chunked_callback=None` parameters for compatibility

