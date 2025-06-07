import uuid
from django.utils.text import slugify
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
import io
import requests
from django.core.files.base import ContentFile


class ImageProcessor:
    """Image processing utilities for content optimization"""

    @staticmethod
    def optimize_image_for_web(image_url, width=800, height=600, quality=85):
        """
        Optimize image for web using Cloudinary transformations

        Args:
            image_url (str): Source image URL
            width (int): Target width
            height (int): Target height
            quality (int): Image quality (1-100)

        Returns:
            str: Optimized image URL
        """
        try:
            if "cloudinary.com" in image_url:
                # Already a Cloudinary URL, apply transformations
                transformed_url = cloudinary.CloudinaryImage(image_url).build_url(
                    width=width,
                    height=height,
                    crop="fill",
                    quality=quality,
                    format="auto",
                    fetch_format="auto",
                )
                return transformed_url
            else:
                # External URL, upload to Cloudinary and optimize
                result = cloudinary.uploader.upload(
                    image_url,
                    transformation={
                        "width": width,
                        "height": height,
                        "crop": "fill",
                        "quality": quality,
                        "format": "auto",
                        "fetch_format": "auto",
                    },
                )
                return result.get("secure_url", image_url)
        except Exception as e:
            print(f"Error optimizing image: {e}")
            return image_url

    @staticmethod
    def generate_thumbnails(image_url, sizes=None):
        """
        Generate multiple thumbnail sizes

        Args:
            image_url (str): Source image URL
            sizes (list): List of (width, height) tuples

        Returns:
            dict: Dictionary of size -> URL mappings
        """
        if sizes is None:
            sizes = [(150, 150), (300, 300), (600, 400), (1200, 800)]

        thumbnails = {}

        for width, height in sizes:
            size_key = f"{width}x{height}"
            try:
                thumbnail_url = ImageProcessor.optimize_image_for_web(
                    image_url, width, height, quality=90
                )
                thumbnails[size_key] = thumbnail_url
            except Exception as e:
                print(f"Error generating thumbnail {size_key}: {e}")
                thumbnails[size_key] = image_url

        return thumbnails

    @staticmethod
    def extract_dominant_colors(image_url, num_colors=5):
        """
        Extract dominant colors from an image

        Args:
            image_url (str): Image URL
            num_colors (int): Number of colors to extract

        Returns:
            list: List of RGB color tuples
        """
        try:
            response = requests.get(image_url, timeout=10)
            image = Image.open(io.BytesIO(response.content))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize for faster processing
            image.thumbnail((150, 150))

            # Get color palette
            colors = image.getcolors(maxcolors=256 * 256 * 256)
            if colors:
                # Sort by frequency and get top colors
                colors.sort(reverse=True)
                dominant_colors = [color[1] for color in colors[:num_colors]]
                return dominant_colors

        except Exception as e:
            print(f"Error extracting colors from image: {e}")

        return []

    @staticmethod
    def generate_responsive_srcset(image_url, breakpoints=None):
        """
        Generate responsive srcset for different screen sizes

        Args:
            image_url (str): Source image URL
            breakpoints (list): List of widths for responsive images

        Returns:
            str: srcset string for HTML img element
        """
        if breakpoints is None:
            breakpoints = [320, 480, 768, 1024, 1366, 1920]

        srcset_parts = []

        for width in breakpoints:
            try:
                responsive_url = ImageProcessor.optimize_image_for_web(
                    image_url, width=width, height=int(width * 0.75), quality=85
                )
                srcset_parts.append(f"{responsive_url} {width}w")
            except Exception as e:
                print(f"Error generating responsive image for {width}w: {e}")

        return ", ".join(srcset_parts)


def generate_public_id(instance, *args, **kwargs):
    title = instance.title
    unique_id = str(uuid.uuid4()).replace("-", "")
    if not title:
        return unique_id
    slug = slugify(title)
    unique_id_short = unique_id[:5]
    return f"{slug}-{unique_id_short}"


def get_public_id_prefix(instance, *args, **kwargs):
    if hasattr(instance, "path"):
        path = instance.path
        if path.startswith("/"):
            path = path[1:]
        if path.endswith("/"):
            path = path[:-1]
        return path
    public_id = instance.public_id
    model_class = instance.__class__
    model_name = model_class.__name__
    model_name_slug = slugify(model_name)
    if not public_id:
        return f"{model_name_slug}"
    return f"{model_name_slug}/{public_id}"


# def get_display_name(instance, *args, **kwargs):
#     if hasattr(instance, 'get_display_name'):
#         return instance.get_display_name()
#     elif hasattr(instance, 'title'):
#         return instance.title
#     model_class = instance.__class__
#     model_name = model_class.__name__
#     return f"{model_name} Upload"


def get_display_name(instance, *args, **kwargs):
    if hasattr(instance, "get_display_name"):
        return instance.get_display_name()
    elif hasattr(instance, "title"):
        return instance.title
    elif hasattr(instance, "name"):  # Assuming 'name' holds the desired image name
        return instance.name
    elif hasattr(instance, "slug"):  # Assuming 'name' holds the desired image slug
        return instance.slug
    model_class = instance.__class__
    model_name = model_class.__name__
    return f"{model_name} Upload"
