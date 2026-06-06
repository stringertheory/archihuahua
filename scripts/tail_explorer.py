"""Interactive explorer for the lowercase `l` tail.

    .venv/bin/streamlit run scripts/tail_explorer.py

Drag the sliders to shape the tail and see it live, in context, at any weight
and width. Nothing is recompiled per change, so it updates in real time. When
you like a shape, copy the command at the bottom to bake it into the source.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from preview import render_word

st.set_page_config(page_title="Archihuahua l-tail explorer", layout="wide")
st.title("Archihuahua — lowercase `l` tail explorer")

with st.sidebar:
    text = st.text_input("Sample text", "Albert AI Al")

    st.markdown("### Tail shape")
    st.caption("All as ratios of the stem width, so they scale across weights/widths.")
    overhang = st.slider("overhang — reach past the stem", 0.0, 1.0, 0.50, 0.01,
                         help="t = 0.75")
    terminal = st.slider("terminal — height of the upturned tip", 0.0, 1.0, 0.62, 0.01,
                         help="t = 0.72")
    dip = st.slider("dip — below the baseline", 0.0, 0.30, 0.10, 0.01)

    st.markdown("### Instance")
    wght = st.slider("weight (wght)", 100, 900, 700, 10)
    wdth = st.slider("width (wdth)", 62, 125, 100, 1)

fig, ax = plt.subplots(figsize=(14, 4))
render_word(text, wght, wdth, overhang, terminal, dip, ax=ax)
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.markdown("**Bake this shape into the source:**")
st.code(
    "python scripts/add_l_tail.py sources/Archihuahua.glyphs build/out.glyphs "
    f"--overhang {overhang:.2f} --terminal {terminal:.2f} --dip {dip:.2f}",
    language="bash",
)
st.caption("For reference, the `t` tail is overhang 0.75 / terminal 0.72.")
