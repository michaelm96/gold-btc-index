import altair as alt
import pandas as pd
import streamlit as st

SCORE_SCALE = alt.Scale(domain=[0, 100])


def line_chart(series, title, y_title, scale=alt.Undefined, rules=()):
    if series.empty:
        st.caption(f"**{title}**: no data for these years")
        return
    df = series.rename("value").rename_axis("date").reset_index()
    y = alt.Y("value:Q", title=y_title, scale=scale)
    # year ticks for long spans; month ticks when zoomed to a few years (year ticks would leave the axis blank)
    axis = alt.Axis(format="%Y", tickCount="year") if df.date.dt.year.nunique() > 3 else alt.Axis(format="%b %Y")
    base = alt.Chart(df).encode(x=alt.X("date:T", title=None, axis=axis), y=y)
    # hover anywhere in the plot: highlight + tooltip for the nearest month
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", clear="pointerout", empty=False)
    points = base.mark_point(filled=True, size=60).encode(
        opacity=alt.when(hover).then(alt.value(1)).otherwise(alt.value(0)),
        tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"), alt.Tooltip("value:Q", title=y_title, format=",.1f")],
    ).add_params(hover)
    chart = base.mark_line(strokeWidth=2) + points
    if rules:
        # mid-gray: visible on light and dark themes
        guides = alt.Chart(pd.DataFrame({"y": list(rules)})).mark_rule(strokeDash=[4, 4], color="#8a8a8a").encode(y="y:Q")
        chart = chart + guides
    st.altair_chart(chart.properties(title=title, height=260), width="stretch")
