from six import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg


def fig_to_png_string(fig):

    FigureCanvasAgg(fig)
    f = BytesIO()
    fig.savefig(f, format="png")

    return f.getvalue()
