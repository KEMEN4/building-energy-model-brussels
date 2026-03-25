"""
Geometry module for the simplified building energy model.

The geometric properties are taken directly from the reference
building data extracted from the article.

The building is a narrow terraced house:
- only the front and rear façades are exposed
- surfaces are not recomputed from guessed dimensions
"""

from building_data import A_wall, A_window, A_roof, A_ground


def compute_geometry():
    """
    Return the building geometric properties used by the model.

    Returns
    -------
    dict
        Dictionary containing:
        - A_wall_total : total external wall area [m²]
        - A_wall_opaque : opaque wall area [m²]
        - A_window : window area [m²]
        - A_roof : roof area [m²]
        - A_ground : ground/contact floor area [m²]
    """

    A_wall_opaque = A_wall - A_window

    if A_wall_opaque < 0:
        raise ValueError("Opaque wall area cannot be negative. Check A_wall and A_window.")

    return {
        "A_wall_total": A_wall,
        "A_wall_opaque": A_wall_opaque,
        "A_window": A_window,
        "A_roof": A_roof,
        "A_ground": A_ground,
    }


if __name__ == "__main__":
    geom = compute_geometry()

    print("Geometry data:")
    for key, value in geom.items():
        print(f"{key} = {value}")
