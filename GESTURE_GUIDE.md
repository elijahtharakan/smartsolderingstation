# Gesture Recognition Guide

## Available Gestures

The system recognizes the following hand gestures with optional directional movement:

### Basic Gestures (Static)

### 1. **Fist** (0 fingers extended)
- Close all fingers into a fist
- **Action**: Turn relay OFF (gpio:17:off)
- **Use case**: Stop/disable device

### 2. **One Finger** (1 finger extended)
- Extend index finger, keep others closed
- **Action**: Servo position 0.2 (servo:18:0.2)
- **Use case**: Low temperature setting

### 3. **Two Fingers** (2 fingers extended)  
- Extend index and middle fingers (peace sign)
- **Action**: Servo position 0.4 (servo:18:0.4)
- **Use case**: Medium-low temperature

### 4. **Three Fingers** (3 fingers extended)
- Extend index, middle, and ring fingers
- **Action**: Servo position 0.6 (servo:18:0.6)
- **Use case**: Medium temperature

### 5. **Four Fingers** (4 fingers extended)
- Extend all fingers except thumb
- **Action**: Servo position 0.8 (servo:18:0.8)
- **Use case**: Medium-high temperature

### 6. **Five Fingers** (open hand, all 5 fingers extended)
- Fully open hand with all fingers extended
- **Action**: Servo position 1.0 (servo:18:1.0)
- **Use case**: Maximum temperature/fully open

### 7. **Pinch** (thumb and index touching)
- Touch thumb tip to index finger tip
- **Action**: Turn relay ON (gpio:17:on)
- **Use case**: Enable/activate device

---

## Directional Gestures (Movement-Based)

Hold a gesture and move your hand to trigger directional commands:

### Two Fingers + Movement
- **Two + Left**: Pan servo left (servo:12:-0.5)
- **Two + Right**: Pan servo right (servo:12:0.5)
- **Two + Up**: Increase temperature (temp:increase)
- **Two + Down**: Decrease temperature (temp:decrease)

### Three Fingers + Movement
- **Three + Left**: Move left (move:left)
- **Three + Right**: Move right (move:right)
- **Three + Up**: Move forward (move:forward)
- **Three + Down**: Move back (move:back)

### One Finger + Movement
- **One + Left**: Slow speed (speed:slow)
- **One + Right**: Fast speed (speed:fast)

**Tips for Directional Gestures:**
- Hold the gesture steady (e.g., 2 fingers)
- Move your entire hand in the desired direction
- Movement must exceed threshold (about 8% of frame width/height)
- Direction is detected continuously while hand is moving

---

## Calibration

If gesture detection is not accurate:

1. **Run the calibration tool**:
   ```bash
   python calibrate_gestures.py
   ```

2. **Test each gesture** and observe the detected finger count

3. **Adjust the thresholds** in `src/gestures.py`:
   
   **For finger detection:**
   - Find the `count_extended_fingers()` function
   - Modify `angle_threshold` value:
     - **Lower value (e.g., 130)**: Stricter detection, fingers must be very straight
     - **Higher value (e.g., 150)**: More lenient, slightly bent fingers count as extended
   - Current threshold: 140.0 degrees
   
   **For directional detection:**
   - Find `_movement_threshold` at the top of the file
   - Modify the value:
     - **Lower value (e.g., 0.05)**: More sensitive, detects smaller movements
     - **Higher value (e.g., 0.12)**: Less sensitive, requires larger movements
   - Current threshold: 0.08 (8% of frame)

---

## Tips for Better Recognition

### Finger Count:
1. **Lighting**: Ensure good, even lighting on your hand
2. **Background**: Plain, non-skin-colored background works best
3. **Distance**: Keep hand 1-2 feet from camera
4. **Orientation**: Face palm toward camera
5. **Steady**: Hold gesture steady for 0.5 seconds for detection
6. **Clear gestures**: Make distinct finger positions

### Directional Movement:
1. **Hold gesture first**: Establish the finger count before moving
2. **Smooth movement**: Move steadily in one direction
3. **Clear direction**: Move primarily in one axis (left/right or up/down)
4. **Sufficient movement**: Move at least 10-15% of the frame width/height
5. **Reset between**: Stop moving briefly between directional commands

---

## Customization

Edit `config/example_config.yaml` to change what each gesture does:

```yaml
gestures:
  # Basic gestures
  one: "your_custom_command"
  two: "another_command"
  
  # Directional gestures
  two_left: "custom_left_action"
  two_right: "custom_right_action"
  # etc.
```

**Command formats:**
- GPIO control: `gpio:PIN:on` or `gpio:PIN:off`  
- Servo control: `servo:PIN:VALUE` (VALUE: -1.0 to 1.0)
- Custom commands: Any string (will be sent to robot interface)

---

## Troubleshooting

**Problem**: Wrong finger count detected  
**Solution**: Adjust `angle_threshold` in `src/gestures.py` (line ~100)

**Problem**: Thumb not detected as extended  
**Solution**: Increase `thumb_tip_dist` threshold (line with `> 0.15`)

**Problem**: Direction not detecting  
**Solution**: Lower `_movement_threshold` at top of `src/gestures.py` (currently 0.08)

**Problem**: Too many false direction triggers  
**Solution**: Increase `_movement_threshold` to require more movement

**Problem**: Gestures trigger too quickly  
**Solution**: Increase debounce time in `src/demo.py` (change `> 0.5` to higher value)

**Problem**: Pinch not detecting  
**Solution**: Increase `thresh` parameter in `is_pinch()` function (currently 0.05)

---

## Advanced: Custom Directional Gestures

You can add any combination of gesture + direction in the config:

```yaml
gestures:
  four_left: "custom_action_1"
  four_right: "custom_action_2"
  five_up: "maximize_all"
  five_down: "minimize_all"
```

The format is always: `{gesture}_{direction}`  
Where gesture is: `fist`, `one`, `two`, `three`, `four`, `five`, `pinch`  
And direction is: `left`, `right`, `up`, `down`
