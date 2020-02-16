import matplotlib.pyplot as plt


def my_plot(x_array, y_array, xlab, ylab, title):
    fig, ax = plt.subplots()
    ax.plot(x_array, y_array)
    ax.set_ylabel(ylab)
    ax.set_xlabel(xlab)
    ax.set_title(title)

    return fig

def my_save_plot(fig, file_name):
    fig.savefig(file_name)
