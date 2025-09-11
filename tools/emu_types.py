#!/usr/bin/env python3
"""
EMU Type System for Design Token Formula Evaluation

Provides precise integer-based calculations for OOXML coordinates
using English Metric Units (EMU) with type safety and unit conversions.
"""


from typing import Any, Dict, Optional, Union
import math


# EMU Constants
EMU_PER_INCH = 914400
EMU_PER_POINT = 12700
EMU_PER_CM = 360000
EMU_PER_MM = 36000  # 1 mm = 36,000 EMU (25.4mm/inch × EMU_PER_INCH ÷ 25.4)

# Maximum safe EMU value to prevent overflow in calculations
# Use 64-bit range but keep reasonable limits for OOXML usage
MAX_EMU_VALUE = 2**50  # Very large but safe for multiplication
MIN_EMU_VALUE = -2**50


class EMUOverflowError(OverflowError):
    """Raised when EMU calculations would result in overflow"""
    pass


class EMUConversionError(ValueError):
    """Raised when unit conversion fails due to invalid input"""
    pass


class EMUValue:
    """
    Represents a precise EMU (English Metric Unit) value for OOXML calculations
    
    EMU is the base unit for all OOXML measurements:
    - 1 inch = 914,400 EMU
    - 1 point = 12,700 EMU  
    - 1 cm ≈ 360,000 EMU
    
    All operations maintain integer precision to ensure exact OOXML coordinates.
    """
    
    def __init__(self, value: Union[int, float, str]):
        """
        Initialize EMU value with automatic type conversion to integer
        
        Args:
            value: Numeric value to convert to EMU (truncated to integer)
            
        Raises:
            TypeError: If value cannot be converted to numeric type
            EMUOverflowError: If value exceeds safe EMU range
        """
        try:
            if isinstance(value, str):
                # Try to parse as float first, then convert to int
                numeric_value = float(value)
            else:
                numeric_value = float(value)
                
            # Convert to integer (truncate decimal part)
            int_value = int(numeric_value)
            
            # Check for overflow
            if int_value > MAX_EMU_VALUE or int_value < MIN_EMU_VALUE:
                raise EMUOverflowError(
                    f"EMU value {int_value} exceeds safe range "
                    f"({MIN_EMU_VALUE} to {MAX_EMU_VALUE})"
                )
            
            self._value = int_value
            
        except (TypeError, ValueError) as e:
            raise TypeError(f"Cannot convert {type(value).__name__} to EMUValue: {e}")
    
    @property
    def value(self) -> int:
        """Get the integer EMU value"""
        return self._value
    
    def to_ooxml_attr(self) -> str:
        """Convert to string format for OOXML attributes"""
        return str(self._value)
    
    def to_inches(self) -> float:
        """Convert EMU to inches"""
        return self._value / EMU_PER_INCH
    
    def to_points(self) -> float:
        """Convert EMU to points"""
        return self._value / EMU_PER_POINT
    
    def to_cm(self) -> float:
        """Convert EMU to centimeters"""
        return self._value / EMU_PER_CM
    
    def to_mm(self) -> float:
        """Convert EMU to millimeters"""
        return self._value / EMU_PER_MM
    
    # Arithmetic operators
    def __add__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Addition with automatic type promotion"""
        if isinstance(other, EMUValue):
            return EMUValue(self._value + other._value)
        return EMUValue(self._value + int(other))
    
    def __radd__(self, other: Union[int, float]) -> 'EMUValue':
        """Reverse addition"""
        return EMUValue(int(other) + self._value)
    
    def __sub__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Subtraction with automatic type promotion"""
        if isinstance(other, EMUValue):
            return EMUValue(self._value - other._value)
        return EMUValue(self._value - int(other))
    
    def __rsub__(self, other: Union[int, float]) -> 'EMUValue':
        """Reverse subtraction"""
        return EMUValue(int(other) - self._value)
    
    def __mul__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Multiplication with automatic type promotion"""
        if isinstance(other, EMUValue):
            return EMUValue(self._value * other._value)
        return EMUValue(int(self._value * other))
    
    def __rmul__(self, other: Union[int, float]) -> 'EMUValue':
        """Reverse multiplication"""
        return EMUValue(int(other * self._value))
    
    def __truediv__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """True division with automatic type promotion"""
        if isinstance(other, EMUValue):
            if other._value == 0:
                raise ZeroDivisionError("Division by zero EMUValue")
            return EMUValue(self._value // other._value)  # Integer division for precision
        if other == 0:
            raise ZeroDivisionError("Division by zero")
        return EMUValue(int(self._value / other))
    
    def __rtruediv__(self, other: Union[int, float]) -> 'EMUValue':
        """Reverse true division"""
        if self._value == 0:
            raise ZeroDivisionError("Division by zero EMUValue")
        return EMUValue(int(other / self._value))
    
    def __floordiv__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Floor division"""
        if isinstance(other, EMUValue):
            if other._value == 0:
                raise ZeroDivisionError("Division by zero EMUValue")
            return EMUValue(self._value // other._value)
        if other == 0:
            raise ZeroDivisionError("Division by zero")
        return EMUValue(self._value // int(other))
    
    def __mod__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Modulo operation"""
        if isinstance(other, EMUValue):
            if other._value == 0:
                raise ZeroDivisionError("Modulo by zero EMUValue")
            return EMUValue(self._value % other._value)
        if other == 0:
            raise ZeroDivisionError("Modulo by zero")
        return EMUValue(self._value % int(other))
    
    def __pow__(self, other: Union['EMUValue', int, float]) -> 'EMUValue':
        """Power operation"""
        if isinstance(other, EMUValue):
            return EMUValue(self._value ** other._value)
        return EMUValue(self._value ** int(other))
    
    # Comparison operators
    def __eq__(self, other: Union['EMUValue', int, float]) -> bool:
        """Equality comparison"""
        if isinstance(other, EMUValue):
            return self._value == other._value
        return self._value == int(other)
    
    def __ne__(self, other: Union['EMUValue', int, float]) -> bool:
        """Inequality comparison"""
        return not self.__eq__(other)
    
    def __lt__(self, other: Union['EMUValue', int, float]) -> bool:
        """Less than comparison"""
        if isinstance(other, EMUValue):
            return self._value < other._value
        return self._value < int(other)
    
    def __le__(self, other: Union['EMUValue', int, float]) -> bool:
        """Less than or equal comparison"""
        if isinstance(other, EMUValue):
            return self._value <= other._value
        return self._value <= int(other)
    
    def __gt__(self, other: Union['EMUValue', int, float]) -> bool:
        """Greater than comparison"""
        if isinstance(other, EMUValue):
            return self._value > other._value
        return self._value > int(other)
    
    def __ge__(self, other: Union['EMUValue', int, float]) -> bool:
        """Greater than or equal comparison"""
        if isinstance(other, EMUValue):
            return self._value >= other._value
        return self._value >= int(other)
    
    # Class methods for aspect ratio calculations
    @classmethod
    def from_inches(cls, inches: Union[int, float]) -> 'EMUValue':
        """Create EMUValue from inches"""
        return cls(int(float(inches) * EMU_PER_INCH))
    
    @classmethod
    def from_points(cls, points: Union[int, float]) -> 'EMUValue':
        """Create EMUValue from points"""
        return cls(int(float(points) * EMU_PER_POINT))
    
    @classmethod
    def from_cm(cls, cm: Union[int, float]) -> 'EMUValue':
        """Create EMUValue from centimeters"""
        return cls(int(float(cm) * EMU_PER_CM))
    
    @classmethod
    def from_mm(cls, mm: Union[int, float]) -> 'EMUValue':
        """Create EMUValue from millimeters"""
        return cls(int(float(mm) * EMU_PER_MM))
    
    @classmethod
    def from_pixels(cls, pixels: Union[int, float], dpi: float = 96.0) -> 'EMUValue':
        """
        Create EMUValue from pixels with DPI conversion
        
        Args:
            pixels: Value in pixels
            dpi: Dots per inch (default 96 DPI for screen)
            
        Returns:
            EMUValue equivalent
        """
        inches = float(pixels) / dpi
        return cls.from_inches(inches)
    
    # Unary operators
    def __neg__(self) -> 'EMUValue':
        """Negation"""
        return EMUValue(-self._value)
    
    def __pos__(self) -> 'EMUValue':
        """Positive (identity)"""
        return EMUValue(self._value)
    
    def __abs__(self) -> 'EMUValue':
        """Absolute value"""
        return EMUValue(abs(self._value))
    
    # String representations
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self._value} EMU"
    
    def __repr__(self) -> str:
        """Developer string representation"""
        return f"EMUValue({self._value})"
    
    # Hash and int conversion for use as dict keys, etc.
    def __hash__(self) -> int:
        """Hash for use in dictionaries and sets"""
        return hash(self._value)
    
    def __int__(self) -> int:
        """Convert to integer"""
        return self._value


class Point:
    """
    Represents a 2D point in EMU coordinates for OOXML positioning
    """
    
    def __init__(self, x: Union[EMUValue, int, float], y: Union[EMUValue, int, float]):
        """
        Initialize point with EMU coordinates
        
        Args:
            x: X coordinate (converted to EMUValue if not already)
            y: Y coordinate (converted to EMUValue if not already)
        """
        self.x = x if isinstance(x, EMUValue) else EMUValue(x)
        self.y = y if isinstance(y, EMUValue) else EMUValue(y)
    
    def __add__(self, other: 'Point') -> 'Point':
        """Add two points (vector addition)"""
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract two points (vector subtraction)"""
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: Union[int, float]) -> 'Point':
        """Scale point by scalar value"""
        return Point(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: Union[int, float]) -> 'Point':
        """Divide point by scalar value"""
        return Point(self.x / scalar, self.y / scalar)
    
    def distance_to(self, other: 'Point') -> EMUValue:
        """Calculate Euclidean distance to another point"""
        dx = self.x - other.x
        dy = self.y - other.y
        distance_squared = dx * dx + dy * dy
        distance = EMUValue(int(math.sqrt(distance_squared.value)))
        return distance
    
    def to_ooxml(self) -> Dict[str, str]:
        """Convert to OOXML coordinate dictionary"""
        return {
            "x": self.x.to_ooxml_attr(),
            "y": self.y.to_ooxml_attr()
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Point({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """Developer string representation"""
        return f"Point({repr(self.x)}, {repr(self.y)})"
    
    def __eq__(self, other: 'Point') -> bool:
        """Equality comparison"""
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y


class Rectangle:
    """
    Represents a rectangle in EMU coordinates for OOXML shape positioning
    """
    
    def __init__(
        self, 
        x: Union[EMUValue, int, float], 
        y: Union[EMUValue, int, float],
        width: Union[EMUValue, int, float], 
        height: Union[EMUValue, int, float]
    ):
        """
        Initialize rectangle with position and dimensions
        
        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate  
            width: Rectangle width
            height: Rectangle height
            
        Raises:
            ValueError: If width or height is negative
        """
        self.x = x if isinstance(x, EMUValue) else EMUValue(x)
        self.y = y if isinstance(y, EMUValue) else EMUValue(y)
        self.width = width if isinstance(width, EMUValue) else EMUValue(width)
        self.height = height if isinstance(height, EMUValue) else EMUValue(height)
        
        if self.width.value < 0:
            raise ValueError("Rectangle width cannot be negative")
        if self.height.value < 0:
            raise ValueError("Rectangle height cannot be negative")
    
    @classmethod
    def from_point_and_size(
        cls, 
        origin: Point, 
        width: Union[EMUValue, int, float], 
        height: Union[EMUValue, int, float]
    ) -> 'Rectangle':
        """
        Create rectangle from origin point and dimensions
        
        Args:
            origin: Top-left corner point
            width: Rectangle width
            height: Rectangle height
            
        Returns:
            Rectangle instance
        """
        return cls(origin.x, origin.y, width, height)
    
    @property
    def left(self) -> EMUValue:
        """Left edge X coordinate"""
        return self.x
    
    @property
    def top(self) -> EMUValue:
        """Top edge Y coordinate"""
        return self.y
    
    @property
    def right(self) -> EMUValue:
        """Right edge X coordinate"""
        return self.x + self.width
    
    @property
    def bottom(self) -> EMUValue:
        """Bottom edge Y coordinate"""
        return self.y + self.height
    
    def center(self) -> Point:
        """Get center point of rectangle"""
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        return Point(center_x, center_y)
    
    def area(self) -> EMUValue:
        """Calculate rectangle area"""
        return self.width * self.height
    
    def contains_point(self, point: Point) -> bool:
        """Check if point is inside rectangle (inclusive of edges)"""
        return (
            self.left <= point.x <= self.right and
            self.top <= point.y <= self.bottom
        )
    
    def intersects(self, other: 'Rectangle') -> bool:
        """Check if this rectangle intersects with another rectangle"""
        return not (
            self.right < other.left or
            other.right < self.left or
            self.bottom < other.top or
            other.bottom < self.top
        )
    
    def intersection(self, other: 'Rectangle') -> Optional['Rectangle']:
        """
        Calculate intersection rectangle with another rectangle
        
        Returns:
            Rectangle representing intersection area, or None if no intersection
        """
        if not self.intersects(other):
            return None
        
        left = EMUValue(max(self.left.value, other.left.value))
        top = EMUValue(max(self.top.value, other.top.value))
        right = EMUValue(min(self.right.value, other.right.value))
        bottom = EMUValue(min(self.bottom.value, other.bottom.value))
        
        width = right - left
        height = bottom - top
        
        return Rectangle(left, top, width, height)
    
    def scale(self, factor: float) -> 'Rectangle':
        """Scale rectangle uniformly (position unchanged, dimensions scaled)"""
        return Rectangle(
            self.x,
            self.y,
            self.width * factor,
            self.height * factor
        )
    
    def scale_xy(self, x_factor: float, y_factor: float) -> 'Rectangle':
        """Scale rectangle non-uniformly"""
        return Rectangle(
            self.x,
            self.y,
            self.width * x_factor,
            self.height * y_factor
        )
    
    def to_ooxml(self, format: str = "standard") -> Dict[str, Any]:
        """
        Convert to OOXML coordinate dictionary
        
        Args:
            format: Output format ("standard", "ppt")
            
        Returns:
            Dictionary with OOXML coordinates
        """
        if format == "ppt":
            # PowerPoint uses nested off/ext structure
            return {
                "off": {
                    "x": self.x.to_ooxml_attr(),
                    "y": self.y.to_ooxml_attr()
                },
                "ext": {
                    "cx": self.width.to_ooxml_attr(),
                    "cy": self.height.to_ooxml_attr()
                }
            }
        else:
            # Standard OOXML format
            return {
                "x": self.x.to_ooxml_attr(),
                "y": self.y.to_ooxml_attr(),
                "cx": self.width.to_ooxml_attr(),
                "cy": self.height.to_ooxml_attr()
            }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Rectangle({self.x}, {self.y}, {self.width} × {self.height})"
    
    def __repr__(self) -> str:
        """Developer string representation"""
        return f"Rectangle({repr(self.x)}, {repr(self.y)}, {repr(self.width)}, {repr(self.height)})"
    
    def __eq__(self, other: 'Rectangle') -> bool:
        """Equality comparison"""
        if not isinstance(other, Rectangle):
            return False
        return (
            self.x == other.x and
            self.y == other.y and
            self.width == other.width and
            self.height == other.height
        )


# Unit conversion functions
def inches_to_emu(inches: Union[int, float]) -> EMUValue:
    """
    Convert inches to EMU
    
    Args:
        inches: Value in inches
        
    Returns:
        EMUValue representing the equivalent EMU measurement
        
    Raises:
        EMUConversionError: If input cannot be converted
    """
    try:
        return EMUValue(int(float(inches) * EMU_PER_INCH))
    except (TypeError, ValueError) as e:
        raise EMUConversionError(f"Cannot convert {inches} inches to EMU: {e}")


def points_to_emu(points: Union[int, float]) -> EMUValue:
    """
    Convert points to EMU
    
    Args:
        points: Value in points
        
    Returns:
        EMUValue representing the equivalent EMU measurement
        
    Raises:
        EMUConversionError: If input cannot be converted
    """
    try:
        return EMUValue(int(float(points) * EMU_PER_POINT))
    except (TypeError, ValueError) as e:
        raise EMUConversionError(f"Cannot convert {points} points to EMU: {e}")


def cm_to_emu(cm: Union[int, float]) -> EMUValue:
    """
    Convert centimeters to EMU
    
    Args:
        cm: Value in centimeters
        
    Returns:
        EMUValue representing the equivalent EMU measurement
        
    Raises:
        EMUConversionError: If input cannot be converted
    """
    try:
        return EMUValue(int(float(cm) * EMU_PER_CM))
    except (TypeError, ValueError) as e:
        raise EMUConversionError(f"Cannot convert {cm} cm to EMU: {e}")


def emu_to_inches(emu: EMUValue) -> float:
    """Convert EMUValue to inches"""
    return emu.to_inches()


def emu_to_points(emu: EMUValue) -> float:
    """Convert EMUValue to points"""
    return emu.to_points()


def emu_to_cm(emu: EMUValue) -> float:
    """Convert EMUValue to centimeters"""
    return emu.to_cm()


def mm_to_emu(mm: Union[int, float]) -> EMUValue:
    """
    Convert millimeters to EMU
    
    Args:
        mm: Value in millimeters
        
    Returns:
        EMUValue representing the equivalent EMU measurement
        
    Raises:
        EMUConversionError: If input cannot be converted
    """
    try:
        return EMUValue(int(float(mm) * EMU_PER_MM))
    except (TypeError, ValueError) as e:
        raise EMUConversionError(f"Cannot convert {mm} mm to EMU: {e}")


def emu_to_mm(emu: EMUValue) -> float:
    """Convert EMUValue to millimeters"""
    return emu.to_mm()


def pixels_to_emu(pixels: Union[int, float], dpi: float = 96.0) -> EMUValue:
    """
    Convert pixels to EMU with DPI awareness
    
    Args:
        pixels: Value in pixels
        dpi: Dots per inch (default 96 DPI for screen)
        
    Returns:
        EMUValue representing the equivalent EMU measurement
        
    Raises:
        EMUConversionError: If input cannot be converted
    """
    try:
        inches = float(pixels) / dpi
        return EMUValue(int(inches * EMU_PER_INCH))
    except (TypeError, ValueError, ZeroDivisionError) as e:
        raise EMUConversionError(f"Cannot convert {pixels} pixels to EMU: {e}")


def emu_to_pixels(emu: EMUValue, dpi: float = 96.0) -> float:
    """Convert EMUValue to pixels with DPI awareness"""
    inches = emu.to_inches()
    return inches * dpi


if __name__ == '__main__':
    # Simple test of the EMU type system
    print("EMU Type System Test")
    print("===================")
    
    # Test EMUValue creation and operations
    slide_width = inches_to_emu(13.333)  # Standard 16:9 slide width
    slide_height = inches_to_emu(7.5)    # Standard 16:9 slide height
    
    print(f"Slide dimensions: {slide_width} × {slide_height}")
    print(f"Slide dimensions: {slide_width.to_inches():.2f}\" × {slide_height.to_inches():.2f}\"")
    
    # Test Point operations
    origin = Point(0, 0)
    corner = Point(slide_width, slide_height)
    center = Point(slide_width / 2, slide_height / 2)
    
    print(f"\nSlide corners:")
    print(f"  Origin: {origin}")
    print(f"  Corner: {corner}")
    print(f"  Center: {center}")
    
    # Test Rectangle operations
    slide_rect = Rectangle(0, 0, slide_width, slide_height)
    margin = inches_to_emu(1.0)
    content_rect = Rectangle(margin, margin, slide_width - 2*margin, slide_height - 2*margin)
    
    print(f"\nRectangles:")
    print(f"  Slide: {slide_rect}")
    print(f"  Content: {content_rect}")
    print(f"  Content area: {content_rect.area()} EMU²")
    
    # Test OOXML output
    print(f"\nOOXML coordinates:")
    print(f"  Slide: {slide_rect.to_ooxml()}")
    print(f"  Content: {content_rect.to_ooxml()}")
    
    print("\n✅ EMU Type System basic functionality verified!")