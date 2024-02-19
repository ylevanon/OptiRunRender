import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Load the images
img_a = mpimg.imread("figure_a.png")
img_b = mpimg.imread("figure_b.png")

# Create figure and axes
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

# Set titles for subplots
ax1.set_title("(a)")
ax2.set_title("(b)")

# Display images
ax1.imshow(img_a)
ax2.imshow(img_b)

# Remove axis ticks
ax1.axis("off")
ax2.axis("off")

# Adjust layout
plt.tight_layout()

# Save the figure
plt.savefig("combined_figure.png")

# Show the figure
plt.show()
