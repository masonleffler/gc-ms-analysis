import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from streamlit_sortables import sort_items


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="GC Chromatogram Plotter",
    layout="wide"
)

st.title("GC Chromatogram Plotter")


# ============================================================
# SIX DEFAULT TRACE COLORS
# ============================================================

DEFAULT_COLORS = [
    "#CC6666", #salmon 1
    "#AA0066", #magenta 2 
    "#A067CF", #purple 3
    "#73A8D1", #blue 4
    "#87AE73", # sage 5
    "#006400", #forest green 6
]


# ============================================================
# DEFAULT SAMPLE LABELS
# ============================================================

DEFAULT_LABELS = [
    "Sample 1",
    "Sample 2",
    "Sample 3",
    "Sample 4",
    "Sample 5",
    "Sample 6"
]


# ============================================================
# DEFAULT GRAY REFERENCE ANNOTATIONS
# ============================================================
#
# peak_x = retention-time coordinate of the chromatographic
# feature in the ORIGINAL, unoffset data.
#
# label_x and time_x determine where the text appears.
#
# There is NO reference chromatogram.
#
# The gray annotation is defined geometrically so that it
# follows the same X/Y offset vector used to stack the traces.
# ============================================================

DEFAULT_ANNOTATIONS = [

    {
        "label": "reference 1",
        "rt": 6.91,
        "peak_x": 6.89,
        "label_x": 7.75,
        "time_x": 7.75,
        "anchor": "left"
    }]

    # {
    #     "label": "reference 2",
    #     "rt": 9.14,
    #     "peak_x": 9.164,
    #     "label_x": 9.92,
    #     "time_x": 9.92,
    #     "anchor": "right"}]
#     },

#     {
#         "label": "reference 3",
#         "rt": 9.94,
#         "peak_x": 9.925,
#         "label_x": 10.78,
#         "time_x": 10.78,
#         "anchor": "right"
#     },

#     {
#         "label": "reference 4",
#         "rt": 10.318,
#         "peak_x": 10.305,
#         "label_x": 11.22,
#         "time_x": 11.22,
#         "anchor": "left"
#     }
# ]


# ============================================================
# ROBUST CSV READER
# ============================================================

def read_clean(uploaded_file):

    uploaded_file.seek(0)

    text = uploaded_file.getvalue().decode(
        "utf-8",
        errors="replace"
    )

    lines = text.splitlines()

    if len(lines) < 3:
        raise ValueError(
            f"{uploaded_file.name} does not contain enough rows."
        )

    data = []

    # --------------------------------------------------------
    # Match original R processing:
    #
    # Remove first CSV column.
    # Remove first two rows.
    # Keep first two remaining columns.
    #
    # Therefore:
    #
    # original CSV column 2 -> x
    # original CSV column 3 -> y
    # --------------------------------------------------------

    for line in lines[2:]:

        parts = line.split(",")

        if len(parts) < 3:
            continue

        try:

            x = float(parts[1].strip())
            y = float(parts[2].strip())

            data.append([x, y])

        except (ValueError, TypeError):
            continue

    if not data:

        raise ValueError(
            f"No numerical chromatogram data could be found "
            f"in {uploaded_file.name}."
        )

    return pd.DataFrame(
        data,
        columns=["x", "y"]
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Plot Settings")


# ============================================================
# 1. UPLOAD FILES
# ============================================================

st.sidebar.subheader(
    "1. Upload chromatograms"
)

uploaded_files = st.sidebar.file_uploader(
    "Upload GC CSV files in the order you want them displayed. The bottom trace will correspond to the first file. You'll be able to edit this later, but you'll lose the default colors. The program uses .csv files with data points starting at the third row and the 2nd and third columns; when exporting from MassHunter Qualitative, this is the default format of the .csv file. This package is optimized for samples containing internal standards such that the exported files are normalized to the highest peak in each chromatogram and y values fall between 0 and 100.",
    type=["csv"],
    accept_multiple_files=True
)


# ============================================================
# 2. GLOBAL TRACE OFFSETS
# ============================================================

st.sidebar.subheader(
    "2. Trace offsets"
)

# st.sidebar.markdown(
#     """
# The chromatograms are offset according to their
# **drag-and-drop order**.


#"""
#)

x_offset_increment = st.sidebar.number_input(
    "X offset increment",
    value=0.15,
    step=0.05,
    format="%.3f"
)

y_offset_increment = st.sidebar.number_input(
    "Y offset increment",
    value=5.00,
    step=1.00,
    format="%.2f"
)


# ============================================================
# 3. DRAG-AND-DROP ORDER
# ============================================================

trace_settings = []

if uploaded_files:

    st.sidebar.subheader(
        "3. Drag-and-drop chromatogram order"
    )

    st.sidebar.markdown(
        """
**Drag the files on the rightinto the order you want them plotted.**
The first file will appear on the bottom, and the final file on top.
        """
 )

    # --------------------------------------------------------
    # Create unique IDs
    # --------------------------------------------------------

    file_lookup = {}

    sortable_items = []

    for i, uploaded_file in enumerate(uploaded_files):

        item_id = (
            f"{uploaded_file.name}___{i}"
        )

        file_lookup[item_id] = uploaded_file

        sortable_items.append(item_id)


    # --------------------------------------------------------
    # Initialize saved ordering
    # --------------------------------------------------------

    if "file_order" not in st.session_state:

        st.session_state.file_order = sortable_items

    else:

        previous_order = (
            st.session_state.file_order
        )

        # Remove files that are no longer uploaded

        previous_order = [
            item
            for item in previous_order
            if item in sortable_items
        ]

        # Add newly uploaded files

        for item in sortable_items:

            if item not in previous_order:

                previous_order.append(item)

        st.session_state.file_order = (
            previous_order
        )


    # --------------------------------------------------------
    # Drag-and-drop sorter
    # --------------------------------------------------------

    sorted_items = sort_items(
        st.session_state.file_order,
        key="chromatogram_order"
    )

    st.session_state.file_order = sorted_items


    # --------------------------------------------------------
    # Display current order
    # --------------------------------------------------------

    st.sidebar.markdown(
        "### Individual Trace Settings")
    
    st.sidebar.markdown(    
    "The sample labels correspond to a specific trace, so if you re-order your files, so be sure you are editing the correct trace.")


    # for i, item_id in enumerate(sorted_items):

    #     st.sidebar.write(
    #         f"**{i + 1}.** "
    #         f"{file_lookup[item_id].name}"
    #     )


    # --------------------------------------------------------
    # File-specific settings
    # --------------------------------------------------------

    for plot_index, item_id in enumerate(
        sorted_items
    ):

        uploaded_file = (
            file_lookup[item_id]
        )

        file_name = uploaded_file.name


        # ----------------------------------------------------
        # DEFAULT COLOR
        # ----------------------------------------------------

        color_key = (
            f"trace_color_{item_id}"
        )

        if color_key not in st.session_state:

            if plot_index < len(DEFAULT_COLORS):

                st.session_state[color_key] = (
                    DEFAULT_COLORS[plot_index]
                )

            # else:

            #     st.session_state[color_key] = (
            #         "#000000"
            #     )


        # ----------------------------------------------------
        # DEFAULT LABEL
        # ----------------------------------------------------

        label_key = (
            f"trace_label_{item_id}"
        )

        if label_key not in st.session_state:

            if plot_index < len(DEFAULT_LABELS):

                st.session_state[label_key] = (
                    DEFAULT_LABELS[plot_index]
                )

            else:

                st.session_state[label_key] = (
                    file_name
                )


        # ----------------------------------------------------
        # FILE SETTINGS
        # ----------------------------------------------------

        with st.sidebar.expander(
            f"{plot_index + 1}. {file_name}",
            expanded=False
        ):

            label = st.text_input(
                "Sample label",
                key=label_key
            )

            color = st.color_picker(
                "Trace  and label color",
                key=color_key
            )
            
    

            show_label = st.checkbox(
                "Show sample label",
                value=True,
                key=f"trace_show_{item_id}"
            )


        # ----------------------------------------------------
        # AUTOMATIC OFFSETS
        # ----------------------------------------------------

        x_offset = (
            plot_index
            * x_offset_increment
        )

        y_offset = (
            plot_index
            * y_offset_increment
        )


        trace_settings.append(
            {
                "file": uploaded_file,

                "label": label,

                "color": color,

                "show_label": show_label,

                "plot_index": plot_index + 1,

                "x_offset": x_offset,

                "y_offset": y_offset + 1
            }
        )


# ============================================================
# 4. GLOBAL SAMPLE-LABEL POSITION
# ============================================================

st.sidebar.subheader(
    "4. Sample labels"
)

st.sidebar.markdown(
    """
These settings apply to **all chromatogram labels**.
"""
)

global_label_x = st.sidebar.number_input(
    "X position for all sample labels",
    value=5.5,
    step=0.1,
    format="%.2f"
)

global_label_height = st.sidebar.number_input(
    "Height above each trace",
    value=2.0,
    step=0.1,
    format="%.2f"
)

sample_label_size = st.sidebar.number_input(
    "Sample label size",
    min_value=6,
    max_value=30,
    value=15
)

# ============================================================
# 5. AXES
# ============================================================

st.sidebar.subheader(
    "5. Axes"
)

x_min = st.sidebar.number_input(
    "X minimum",
    value=5.5,
    step=0.1
)

x_max = st.sidebar.number_input(
    "X maximum",
    value=11.75,
    step=0.1
)

y_min = st.sidebar.number_input(
    "Y minimum",
    value=0.0,
    step=1.0
)

y_max = st.sidebar.number_input(
    "Y maximum",
    value=140.0,
    step=1.0
)

data_x_max = st.sidebar.number_input(
    "Discard raw data above retention time",
    value=11.0,
    step=0.1
)

x_title = st.sidebar.text_input(
    "X-axis title",
    value="Retention time (min)"
)

y_title = st.sidebar.text_input(
    "Y-axis title",
    value="relative counts"
)

show_y_axis = st.sidebar.checkbox(
    "Show Y axis",
    value=False
)


# ============================================================
# 6. FIGURE APPEARANCE
# ============================================================

st.sidebar.subheader(
    "6. Figure appearance"
)

plot_height = st.sidebar.number_input(
    "Plot height",
    min_value=300,
    max_value=1200,
    value=650,
    step=50
)

font_size = st.sidebar.number_input(
    "Axis font size",
    min_value=8,
    max_value=30,
    value=16
)

trace_width = st.sidebar.number_input(
    "Chromatogram line width",
    min_value=0.5,
    max_value=10.0,
    value=1.5,
    step=0.25
)


gray_label_size = st.sidebar.number_input(
    "Reference label size",
    min_value=6,
    max_value=30,
    value=13
)

gray_time_size = st.sidebar.number_input(
    "Reference retention-time size",
    min_value=6,
    max_value=25,
    value=10
)



# ============================================================
# 7. GRAY REFERENCE ANNOTATIONS
# ============================================================

st.sidebar.subheader(
    "7. Reference annotations"
)


# ============================================================
# GLOBAL GRAY X MOVEMENT
# ============================================================

# gray_global_x_shift = st.sidebar.number_input(
#     "Move all gray annotations in X",
#     value=0.00,
#     step=0.05,
#     format="%.3f"
# )


# ============================================================
# GRAY STYLE
# ============================================================

gray_color = st.sidebar.color_picker(
    "Annotation color",
    value="#808080"
)

gray_line_opacity = st.sidebar.slider(
    "Line opacity",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05
)

gray_line_width = st.sidebar.number_input(
    "Line width",
    min_value=0.5,
    max_value=10.0,
    value=1.5,
    step=0.25
)


# ============================================================
# GRAY ANNOTATION VERTICAL POSITIONS
# ============================================================

st.sidebar.markdown(
    "### Annotation height"
)

connector_top_fraction = st.sidebar.number_input(
    "Connector top height",
    min_value=0.20,
    max_value=1.00,
    value=0.96,
    step=0.01
)

label_fraction = st.sidebar.number_input(
    "Compound label height",
    min_value=0.20,
    max_value=1.00,
    value=0.94,
    step=0.01
)

time_fraction = st.sidebar.number_input(
    "Retention time height",
    min_value=0.20,
    max_value=1.00,
    value=0.915,
    step=0.005
)


# ============================================================
# NUMBER OF GRAY ANNOTATIONS
# ============================================================

n_annotations = st.sidebar.number_input(
    "Number of annotations",
    min_value=0,
    max_value=20,
    value=1,
    step=1
)

annotation_settings = []


# ============================================================
# GRAY ANNOTATION CONTROLS
# ============================================================

for i in range(int(n_annotations)):

    if i < len(DEFAULT_ANNOTATIONS):

        defaults = (
            DEFAULT_ANNOTATIONS[i]
        )

    else:

        defaults = {
            "label": f"reference {i + 1}",
            "rt": 8.0,
            "peak_x": 8.0,
            "label_x": 8.8,
            "time_x": 8.8,
            "anchor": "right"
        }


    with st.sidebar.expander(
        f"Reference annotation {i + 1}",
        expanded=False
    ):

        show_annotation = st.checkbox(
            "Show annotation",
            value=True,
            key=f"gray_show_{i}"
        )


        annotation_label = st.text_input(
            "Compound name",
            value=defaults["label"],
            key=f"gray_label_{i}"
        )


        retention_time = st.number_input(
            "Retention time",
            value=float(
                defaults["rt"]
            ),
            step=0.01,
            format="%.3f",
            key=f"gray_rt_{i}"
        )


        # ----------------------------------------------------
        # ORIGINAL RETENTION-TIME COORDINATE
        # ----------------------------------------------------

        peak_x = st.number_input(
            "Reference peak start (min) (move to match the line and peak start)",
            value=float(
                defaults["peak_x"]
            ),
            step=0.01,
            format="%.3f",
            key=f"gray_peak_x_{i}"
        )


        # ----------------------------------------------------
        # LABEL POSITION
        # ----------------------------------------------------

        # label_x = st.number_input(
        #     "Compound label position (x)",
        #     value=float(
        #         defaults["label_x"]
        #     ),
        #     step=0.01,
        #     format="%.3f",
        #     key=f"gray_label_x_{i}"
        # )


        # time_x = st.number_input(
        #     "Retention-time label position (x)",
        #     value=float(
        #         defaults["time_x"]
        #     ),
        #     step=0.01,
        #     format="%.3f",
        #     key=f"gray_time_x_{i}"
        # )


        anchor = st.selectbox(
            "Text alignment",
            [
                "left",
                "center",
                "right"
            ],
            index=[
                "left",
                "center",
                "right"
            ].index(
                defaults["anchor"]
            ),
            key=f"gray_anchor_{i}"
        )


        annotation_settings.append(
            {
                "show": show_annotation,

                "label": annotation_label,

                "rt": retention_time,

                "peak_x": peak_x,

                "anchor": anchor
            }
        )


# ============================================================
# CALCULATE GLOBAL GRAY POSITIONS
# ============================================================

y_range = y_max - y_min


# ------------------------------------------------------------
# HIGHEST TRACE BASELINE
# ------------------------------------------------------------
#
# The baseline of each trace is its Y offset.
#
# Example:
#
# Trace 1 -> 0
# Trace 2 -> 5
# Trace 3 -> 10
# ...
#
# Therefore the highest baseline is the largest Y offset.
# ------------------------------------------------------------

if trace_settings:

    highest_trace_baseline = max(
        trace["y_offset"]
        for trace in trace_settings
    )

else:

    highest_trace_baseline = y_min


# ------------------------------------------------------------
# ELBOW = 10% ABOVE HIGHEST TRACE BASELINE
# ------------------------------------------------------------

gray_elbow_y = (
    highest_trace_baseline
    + 0.1 * highest_trace_baseline
)


# ------------------------------------------------------------
# TOP OF VERTICAL CONNECTOR
# ------------------------------------------------------------

connector_top_y = (
    y_min
    + connector_top_fraction * y_range
)


# ------------------------------------------------------------
# GRAY LABEL POSITIONS
# ------------------------------------------------------------

automatic_label_y = (
    y_min
    + label_fraction * y_range
)

automatic_time_y = (
    y_min
    + time_fraction * y_range
)


# ============================================================
# CREATE FIGURE
# ============================================================

fig = go.Figure()

processed_data = []


# ============================================================
# READ AND PLOT CHROMATOGRAMS
# ============================================================

for trace in trace_settings:

    try:

        df = read_clean(
            trace["file"]
        )


        # ----------------------------------------------------
        # Same filtering as original R script
        # ----------------------------------------------------

        df = df[
            df["x"] <= data_x_max
        ].copy()


        # ----------------------------------------------------
        # PRESERVE ORIGINAL COORDINATES
        # ----------------------------------------------------

        df["raw_x"] = df["x"]
        df["raw_y"] = df["y"]


        # ----------------------------------------------------
        # APPLY AUTOMATIC OFFSETS
        # ----------------------------------------------------

        df["x"] = (
            df["raw_x"]
            + trace["x_offset"]
        )

        df["y"] = (
            df["raw_y"]
            + trace["y_offset"]
        )


        df["sample"] = trace["label"]

        df["plot_order"] = (
            trace["plot_index"]
        )

        df["x_offset"] = (
            trace["x_offset"]
        )

        df["y_offset"] = (
            trace["y_offset"]
        )


        processed_data.append(df)


        # ----------------------------------------------------
        # CHROMATOGRAM
        # ----------------------------------------------------

        fig.add_trace(
            go.Scatter(
                x=df["x"],
                y=df["y"],

                mode="lines",

                name=trace["label"],

                line=dict(
                    color=trace["color"],
                    width=trace_width
                ),

                showlegend=False,

                hovertemplate=(
                    "<b>"
                    + trace["label"]
                    + "</b><br>"
                    + "Retention time = %{x:.3f}<br>"
                    + "Counts = %{y:.3f}"
                    + "<extra></extra>"
                )
            )
        )


        # ----------------------------------------------------
        # SAMPLE LABEL
        # ----------------------------------------------------

        if trace["show_label"]:

            label_y = (
                trace["y_offset"]
                + global_label_height
            )


            fig.add_annotation(
                x=global_label_x,

                y=label_y,

                text=(
                    f"<b>{trace['label']}</b>"
                ),

                showarrow=False,

                xanchor="left",
                yanchor="middle",

                font=dict(
                    family="Arial",
                    size=sample_label_size,
                    color=trace["color"]
                )
            )


    except Exception as e:

        st.error(
            f"Could not read "
            f"{trace['file'].name}: {e}"
        )


# ============================================================
# GRAY REFERENCE ANNOTATIONS
# ============================================================
#
# IMPORTANT GEOMETRY
#
# The gray annotation is NOT attached to a particular trace.
#
# Instead, it is defined by a reference data point:
#
#       (peak_x, peak_y)
#
# in the original chromatogram coordinate system.
#
# The traces are translated by:
#
#       ΔX = x_offset_increment
#       ΔY = y_offset_increment
#
# Therefore the gray diagonal has slope:
#
#       m = ΔY / ΔX
#
# A point on trace n is:
#
#       x_n = peak_x + n ΔX
#       y_n = peak_y + n ΔY
#
# Every one of those points lies on the SAME gray line.
#
# When the offsets change, m changes automatically.
#
# The gray annotation therefore continues to pass through the
# corresponding chromatographic data points.
# ============================================================


for annotation in annotation_settings:

    if not annotation["show"]:
        continue


    # ========================================================
    # FIND REFERENCE DATA POINT
    # ========================================================
    #
    # The first chromatogram establishes the unshifted
    # chromatographic Y coordinate.
    #
    # We use RAW coordinates here.
    # ========================================================

    reference_y = None


    if processed_data:

        reference_df = (
            processed_data[0]
        )


        raw_x = (
            reference_df["raw_x"]
            .to_numpy()
        )

        raw_y = (
            reference_df["raw_y"]
            .to_numpy()
        )


        peak_x_raw = (
            annotation["peak_x"]
        )


        # ----------------------------------------------------
        # Make sure the requested X is within the data range
        # ----------------------------------------------------

        if (
            peak_x_raw >= raw_x.min()
            and
            peak_x_raw <= raw_x.max()
        ):

            reference_y = np.interp(
                peak_x_raw,
                raw_x,
                raw_y
            )


    # --------------------------------------------------------
    # If no data point can be found, skip this annotation.
    # --------------------------------------------------------

    if reference_y is None:

        continue


    # ========================================================
    # APPLY GLOBAL X TRANSLATION
    # ========================================================
    #
    # This moves the entire gray annotation horizontally.
    #
    # The Y coordinate remains unchanged.
    # ========================================================

    peak_x_display = (
        peak_x_raw

    )

    peak_y_display = (
        reference_y
    )


    # ========================================================
    # CALCULATE GRAY DIAGONAL SLOPE
    # ========================================================
    #
    # This is exactly the direction in which the traces move.
    # ========================================================

    if abs(x_offset_increment) > 1e-12:

        gray_slope = (
            y_offset_increment
            / x_offset_increment
        )

    else:

        gray_slope = None


    # ========================================================
    # CALCULATE ELBOW X
    # ========================================================
    #
    # The elbow Y is fixed at:
    #
    #     5% above the highest trace baseline.
    #
    # The X coordinate is calculated from the slope.
    #
    # This means the diagonal:
    #
    #     1. starts exactly at the data point
    #     2. has the trace-offset slope
    #     3. ends exactly at the 5% elbow height
    # ========================================================

    if gray_slope is not None:

        if abs(gray_slope) > 1e-12:

            elbow_x = (
                peak_x_display
                + (
                    gray_elbow_y
                    - peak_y_display
                )
                / gray_slope
            )

        else:

            # Zero slope = horizontal connector

            elbow_x = (
                peak_x_display
            )

    else:

        # No X offset means that the stacking direction
        # is vertical.

        elbow_x = (
            peak_x_display
        )


    # ========================================================
    # GRAY DIAGONAL
    # ========================================================

    fig.add_shape(
        type="line",

        x0=peak_x_display,
        y0=peak_y_display+1,

        x1=elbow_x,
        y1=gray_elbow_y+1,

        line=dict(
            color=gray_color,
            width=gray_line_width
        ),

        opacity=gray_line_opacity
    )


    # ========================================================
    # VERTICAL ELBOW CONNECTOR
    # ========================================================

    fig.add_shape(
        type="line",

        x0=elbow_x,
        y0=gray_elbow_y+1,

        x1=elbow_x,
        y1=connector_top_y,

        line=dict(
            color=gray_color,
            width=gray_line_width
        ),

        opacity=gray_line_opacity
    )


    # ========================================================
    # Automatic gray label position
    # ========================================================
    gray_text_gap = 0.02

    if annotation["anchor"] == "left":
        shifted_label_x = (
        elbow_x + gray_text_gap
    )

        shifted_time_x = (
        elbow_x + gray_text_gap
    )
    
    elif annotation["anchor"] == "right":
        shifted_label_x = (
        elbow_x - gray_text_gap)
        
        shifted_time_x = (
        elbow_x - gray_text_gap)
    
    else:
        shifted_label_x = elbow_x
        shifted_time_x = elbow_x

    # ========================================================
    # GRAY COMPOUND LABEL
    # ========================================================

    fig.add_annotation(
        x=shifted_label_x,

        y=automatic_label_y,

        text=(
            f"<b>{annotation['label']}</b>"
        ),

        showarrow=False,

        xanchor=annotation["anchor"],
        yanchor="middle",

        font=dict(
            family="Arial",
            size=gray_label_size,
            color=gray_color
        )
    )


    # ========================================================
    # GRAY RETENTION-TIME LABEL
    # ========================================================

    fig.add_annotation(
        x=shifted_time_x,

        y=automatic_time_y,

        text=(
            f"<b>{annotation['rt']:.2f} min</b>"
        ),

        showarrow=False,

        xanchor=annotation["anchor"],
        yanchor="middle",

        font=dict(
            family="Arial",
            size=gray_time_size,
            color=gray_color
        )
    )


# ============================================================
# FIGURE FORMATTING
# ============================================================

fig.update_layout(

    height=plot_height,

    plot_bgcolor="white",
    paper_bgcolor="white",

    margin=dict(
        l=70,
        r=30,
        t=30,
        b=70
    ),

    font=dict(
        family="Arial",
        size=font_size,
        color="black"
    ),

    showlegend=False,


    # ========================================================
    # X AXIS
    # ========================================================

    xaxis=dict(

        title=dict(
            text=f"<b>{x_title}</b>",

            font=dict(
                family="Arial",
                size=font_size,
                color = "black"
            )
        ),

        range=[
            x_min,
            x_max
        ],

        showline=True,

        linewidth=1.5,

        linecolor="black",

        # IMPORTANT:
        # Put the axis underneath the chromatograms so the
        # y = 0 trace does not look thinner.

        layer="below traces",

        ticks="outside",

        tickcolor="black",

        showgrid=False,

        zeroline=False,

        tickfont=dict(
            family="Arial",
            size=font_size,
            color="black"
        )
    ),


    # ========================================================
    # Y AXIS
    # ========================================================

    yaxis=dict(

        title=dict(
            text=(
                f"<b>{y_title}</b>"
                if show_y_axis
                else ""
            ),

            font=dict(
                family="Arial",
                size=font_size
            )
        ),

        range=[
            y_min,
            y_max
        ],

        showline=show_y_axis,

        showticklabels=show_y_axis,

        ticks=(
            "outside"
            if show_y_axis
            else ""
        ),

        linewidth=1.5,

        linecolor="black",

        showgrid=False,

        zeroline=False,

        tickfont=dict(
            family="Arial",
            size=font_size,
            color="black"
        )
    )
)


# ============================================================
# DISPLAY PLOT
# ============================================================

if uploaded_files:

    st.plotly_chart(
        fig,

        use_container_width=True,

        config={
            "displaylogo": False,

            "toImageButtonOptions": {
                "format": "svg",
                "filename": "chromatogram",
                "scale": 1
            }
        }
    )


# ============================================================
# OFFSET TABLE
# ============================================================

if trace_settings:

    st.subheader(
        "Chromatogram order and applied offsets"
    )


    offset_table = pd.DataFrame(
        [
            {
                "Position": trace["plot_index"],

                "Sample": trace["label"],

                "File": trace["file"].name,

                "X offset": trace["x_offset"],

                "Y offset": trace["y_offset"]
            }

            for trace in trace_settings
        ]
    )


    st.dataframe(
        offset_table,

        use_container_width=True,

        hide_index=True
    )


# ============================================================
# PROCESSED DATA
# ============================================================

if processed_data:

    df_all = pd.concat(
        processed_data,
        ignore_index=True
    )


    with st.expander(
        "View processed chromatogram data"
    ):

        st.dataframe(
            df_all,

            use_container_width=True
        )


    csv = (
        df_all
        .to_csv(index=False)
        .encode("utf-8")
    )


    st.download_button(
        label="Download processed data as CSV",

        data=csv,

        file_name=(
            "processed_chromatograms.csv"
        ),

        mime="text/csv"
    )


# ============================================================
# NO FILES
# ============================================================

else:

    st.info(
        "Upload one or more chromatogram CSV files "
        "using the sidebar."
    )
