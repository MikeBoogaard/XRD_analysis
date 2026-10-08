import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as patches





def thesis_colormap(n=10):

    gradient_colors = [
        (30/255, 20/255, 75/255),     # deep purple
        (184/255, 115/255, 51/255),   # copper brown
        (255/255, 159/255, 0/255),    # bright orange
        (255/255, 239/255, 213/255),  # papaya whip
    ]
    cmap = LinearSegmentedColormap.from_list("thesis_colormap", gradient_colors)

    # Sample n discrete colors
    sampled_colors = [cmap(i/(n-1)) for i in range(n)]
    hex_colors = [mcolors.to_hex(c) for c in sampled_colors]

    # --- Figure 1: Gradient swatches ---
    fig, ax = plt.subplots(figsize=(12, 2))
    for i, c in enumerate(sampled_colors):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=c))

    # Add labels for all original gradient colors regardless of number
    for j, rgb in enumerate(gradient_colors):
        pos = j / (len(gradient_colors)-1)
        idx = int(round(pos * (n-1)))
        label = f"RGB{tuple(int(x*255) for x in rgb)}"
        ax.text(idx + 0.5, 1.05, label, ha='center', va='bottom', fontsize=8, rotation=45)

    ax.set_xlim(0, len(sampled_colors))
    ax.set_ylim(0, 1.3)
    ax.axis('off')
    plt.show()
    fig.set_size_inches(12,4)
    # --- Figure 2: Stained glass preview ---
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    ax.axis("off")

    shapes = [
        ((0, 0), 1, 1),
        ((1, 0), 1, 0.7),
        ((1, 0.7), 1, 1.3),
        ((0, 1), 1, 1),
    ]

    for i, (xy, w, h) in enumerate(shapes):
        color = gradient_colors[i % len(gradient_colors)]
        rect = patches.Rectangle(xy, w, h, linewidth=3, edgecolor="black", facecolor=color)
        ax.add_patch(rect)

    plt.show()

    return hex_colors