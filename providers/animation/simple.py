from __future__ import annotations

from providers.base import AnimationProvider


class PassthroughAnimation(AnimationProvider):
    def animate_images(self, image_paths, motion_plan):
        return image_paths
