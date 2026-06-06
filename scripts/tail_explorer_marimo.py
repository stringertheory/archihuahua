"""Interactive explorer for the lowercase `l` tail (marimo version).

    marimo edit scripts/tail_explorer_marimo.py     # to play / edit
    marimo run  scripts/tail_explorer_marimo.py     # read-only app

Same idea as the Streamlit explorer (tail_explorer.py): drag the sliders to
shape the tail and see it live, in context, at any weight and width. Nothing is
recompiled per change, so it updates in real time.
"""
import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    import sys

    # make the sibling preview.py importable however marimo is launched
    here = (os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals()
            else os.path.join(os.getcwd(), "scripts"))
    if here not in sys.path:
        sys.path.insert(0, here)

    import marimo as mo
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from preview import render_word
    return mo, plt, render_word


@app.cell
def _(mo):
    mo.md(
        """
        # Archihuahua — lowercase `l` tail explorer
        Drag the sliders to shape the tail and see it live, in context, at any
        weight and width. The `l` is drawn directly (no font build), so it
        updates in real time.
        """
    )
    return


@app.cell
def _(mo):
    text = mo.ui.text(value="Albert AI Al", label="Sample text", full_width=True)
    overhang = mo.ui.slider(0.0, 1.0, 0.01, value=0.39,
                            label="overhang — reach past the stem (t = 0.75)")
    terminal = mo.ui.slider(0.0, 1.0, 0.01, value=0.78,
                            label="terminal — height of the upturned tip (t = 0.72)")
    dip = mo.ui.slider(0.0, 0.30, 0.01, value=0.10, label="dip — below the baseline")
    wght = mo.ui.slider(100, 900, 10, value=700, label="weight (wght)")
    wdth = mo.ui.slider(62, 125, 1, value=100, label="width (wdth)")

    mo.vstack([
        text,
        mo.md("**Tail shape** — all as ratios of the stem width"),
        overhang, terminal, dip,
        mo.md("**Instance**"),
        wght, wdth,
    ])
    return dip, overhang, terminal, text, wdth, wght


@app.cell
def _(dip, overhang, plt, render_word, terminal, text, wdth, wght):
    fig, ax = plt.subplots(figsize=(14, 4))
    render_word(text.value, wght.value, wdth.value,
                overhang.value, terminal.value, dip.value, ax=ax)
    fig
    return


@app.cell
def _(dip, mo, overhang, terminal):
    cmd = ("python scripts/add_l_tail.py sources/Archihuahua.glyphs build/out.glyphs "
           f"--overhang {overhang.value:.2f} --terminal {terminal.value:.2f} "
           f"--dip {dip.value:.2f}")
    mo.md(f"**Bake this shape into the source:**\n\n```bash\n{cmd}\n```")
    return


if __name__ == "__main__":
    app.run()
