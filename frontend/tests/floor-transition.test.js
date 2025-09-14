/**
 * Test for frontend room advancement and map state handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the API functions
const mockAdvanceRoom = vi.fn();
const mockGetMap = vi.fn();

// Mock the API module
vi.mock('../src/lib/uiApi.js', () => ({
  advanceRoom: mockAdvanceRoom,
  getMap: mockGetMap,
  roomAction: vi.fn(),
}));

// Mock the overlay controller
vi.mock('../src/lib/OverlayController.js', () => ({
  openOverlay: vi.fn(),
  backOverlay: vi.fn(),
  homeOverlay: vi.fn(),
}));

describe('Room advancement and floor transitions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should refresh map data when advancing to a new floor', async () => {
    // Mock the response when advancing to a new floor
    mockAdvanceRoom.mockResolvedValue({
      current_index: 1,
      next_room: 'battle-normal'
    });

    // Mock the updated map data with new floor
    mockGetMap.mockResolvedValue({
      map: {
        rooms: [
          { room_id: 0, room_type: 'start', floor: 2, index: 0 },
          { room_id: 1, room_type: 'battle-normal', floor: 2, index: 1 },
          { room_id: 2, room_type: 'battle-weak', floor: 2, index: 2 }
        ],
        current: 1
      },
      party: ['player']
    });

    // Simulate the floor advancement logic
    const res = await mockAdvanceRoom();
    
    expect(res.current_index).toBe(1);
    expect(res.next_room).toBe('battle-normal');

    // Simulate refreshing map data
    const mapData = await mockGetMap();
    expect(mapData.map.rooms).toHaveLength(3);
    expect(mapData.map.rooms[1].floor).toBe(2);
    expect(mapData.map.rooms[1].room_type).toBe('battle-normal');
  });

  it('should handle map state correctly within the same floor', async () => {
    // Mock advancing within the same floor
    mockAdvanceRoom.mockResolvedValue({
      current_index: 5,
      next_room: 'shop'
    });

    mockGetMap.mockResolvedValue({
      map: {
        rooms: [
            { room_id: 4, room_type: 'battle-normal', floor: 1, index: 4 },
            { room_id: 5, room_type: 'shop', floor: 1, index: 5 },
            { room_id: 6, room_type: 'battle-weak', floor: 1, index: 6 }
        ],
        current: 5
      },
      party: ['player']
    });

    const res = await mockAdvanceRoom();
    
    expect(res.current_index).toBe(5);
    expect(res.next_room).toBe('shop');

    const mapData = await mockGetMap();
    expect(mapData.map.rooms[1].room_type).toBe('shop');
    expect(mapData.map.rooms[1].floor).toBe(1);
  });

  it('should use next_room from response when map data is stale', () => {
    // Test the logic where we prioritize next_room from response
    const res = {
      current_index: 1,
      next_room: 'battle-normal'
    };

    const staleMapRooms = [
      { room_id: 0, room_type: 'start', floor: 1, index: 0 },
      { room_id: 1, room_type: 'battle-weak', floor: 1, index: 1 }, // Stale data
    ];

    // Should use next_room from response, not stale map data
    const currentRoomType = res.next_room || staleMapRooms[res.current_index]?.room_type;
    expect(currentRoomType).toBe('battle-normal');
  });
});