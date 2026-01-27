from PySide6.QtCore import QEasingCurve

class AnimConfig:
    # Durations (ms)
    DURATION_INSTANT = 0
    DURATION_FAST = 150    # Microinteractions (hover, press)
    DURATION_NORMAL = 250   # Standard transitions (fade in/out)
    DURATION_SLOW = 400     # Complex movements (slide panels)
    
    # Delays (ms)
    STAGGER_DELAY = 30      # Delay between list items
    
    # Easing Curves
    # OutCubic/Quad is good for entrance (starts fast, slows down)
    EASING_ENTRY = QEasingCurve.OutCubic 
    # InCubic/Quad is good for exit (starts slow, speeds up)
    EASING_EXIT = QEasingCurve.InCubic
    # Sine is good for generic fades
    EASING_Standard = QEasingCurve.InOutSine
    
    # Reduced Motion
    # Can be toggled. If True, durations become 0 or minimal fade.
    REDUCED_MOTION = False 

    @classmethod
    def get_duration(cls, base_duration):
        return 0 if cls.REDUCED_MOTION else base_duration
