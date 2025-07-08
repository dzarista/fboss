# Product Definitions Configuration

This document explains how to configure product definitions for the Thermal Data Converter & Visualizer.

## Overview

Product definitions are stored in `product_definitions.json` and define the specifications for different switch products including port counts, fan counts, and grid layouts.

## File Structure

```json
{
  "products": {
    "product_key": {
      "name": "Display Name",
      "ports": 128,
      "fans": 12,
      "description": "Product description",
      "layoutData": "CSV grid layout"
    }
  },
  "metadata": {
    "version": "1.0",
    "lastUpdated": "2025-01-07",
    "description": "Product definitions for thermal monitoring tools",
    "maxRPM": 11200,
    "defaultProduct": "whistler"
  }
}
```

## Adding a New Product

1. **Open `product_definitions.json`**
2. **Add a new product entry** under the `products` section:

```json
"new_product": {
  "name": "New Product (96 Port, 8 Fans)",
  "ports": 96,
  "fans": 8,
  "description": "New product with 96 ports and 8 fans",
  "layoutData": "1,2,3,4,5,6,7,8\n9,10,11,12,13,14,15,16\n..."
}
```

3. **Define the layout grid** using comma-separated values:
   - Each line represents a row in the visual grid
   - Numbers represent port positions
   - Empty values (between commas) represent gaps
   - Use `\n` to separate rows

## Layout Examples

### Simple 2x4 Layout
```
"layoutData": "1,2,3,4\n5,6,7,8"
```

### Layout with Gaps
```
"layoutData": "1,2,,4\n,6,7,\n9,,11,12"
```

### Whistler 128-Port Layout (8 rows x 16 ports)
```
"layoutData": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16\n17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32\n..."
```

## Product Properties

- **name**: Display name shown in the UI dropdown
- **ports**: Maximum number of ports (determines CSV columns)
- **fans**: Maximum number of fans (determines CSV columns)
- **description**: Optional description for documentation
- **layoutData**: Grid layout for visualization (CSV format with `\n` separators)

## Metadata Properties

- **version**: Configuration file version
- **lastUpdated**: Last modification date
- **description**: File description
- **maxRPM**: Maximum fan RPM for percentage calculations
- **defaultProduct**: Default product selected on page load

## CSV Output Format

Generated CSV files include:
- **datetime** column
- **Fan1/1** through **FanN/1** columns (N = product.fans)
- **DomTemperatureSensor1** through **DomTemperatureSensorN** columns (N = product.ports)

Missing data is filled with "0.00".

## Testing New Products

1. Add the product definition
2. Refresh the web page
3. Check that the new product appears in the dropdown
4. Upload test data and verify CSV generation
5. Switch to visualizer mode and test the grid layout

## Troubleshooting

- **Product not appearing**: Check JSON syntax with a validator
- **Layout issues**: Verify layoutData format and port numbers
- **CSV problems**: Ensure ports/fans counts match your data
- **Loading errors**: Check browser console for error messages

