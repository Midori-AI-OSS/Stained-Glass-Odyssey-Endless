/**
 * Test for room numbering display functionality
 * 
 * This test verifies that room numbers are displayed as 1-based
 * instead of 0-based indices for better user experience.
 */

import { describe, it, expect } from 'vitest';

// Simple isolated test of the roomInfo logic
describe('Room numbering display', () => {
  it('should convert 0-based indices to 1-based room numbers', () => {
    // Simulate the roomInfo logic
    const roomInfo = (mapRooms, currentIndex) => {
      const cur = mapRooms?.[currentIndex] || null;
      return {
        roomNumber: (cur?.index ?? currentIndex ?? 0) + 1,
      };
    };

    // Test room index 0 should display as Room 1
    const result1 = roomInfo([{ index: 0 }], 0);
    expect(result1.roomNumber).toBe(1);

    // Test room index 99 should display as Room 100
    const result2 = roomInfo(Array.from({ length: 100 }, (_, i) => ({ index: i })), 99);
    expect(result2.roomNumber).toBe(100);

    // Test fallback to currentIndex
    const result3 = roomInfo(null, 4);
    expect(result3.roomNumber).toBe(5);
  });
});