import React, { useRef } from 'react';
import { View, Text, StyleSheet, Pressable, Animated } from 'react-native';
import { COLORS, OCCUPANCY_THRESHOLDS } from '../constants';

function ParkingLotCard({ lot, occupancy, capacity, occupiedSpaces, lastUpdated }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const formatTimestamp = (date) => {
    if (!date) return '';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 1.05,
      useNativeDriver: true,
      tension: 100,
      friction: 3,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      tension: 100,
      friction: 3,
    }).start();
  };

  const lotId = lot || 'Unknown';
  const occupancyValue = Math.round(occupancy || 0);
  const capacityValue = capacity != null ? capacity : 'N/A';
  const occupiedValue = occupiedSpaces != null ? occupiedSpaces : 'N/A';

  return (
    <Pressable
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={`Student Parking Lot ${lotId}: ${occupancyValue}% occupied, ${occupiedValue} of ${capacityValue} spaces`}
    >
      <Animated.View
        style={[
          styles.card,
          {
            transform: [{ scale: scaleAnim }],
          }
        ]}
      >
        <Text style={styles.lotName}>Student Parking Lot {lotId}</Text>
        <View
          style={[
            styles.occupancyCircle,
            { borderColor: getOccupancyColor(occupancyValue) }
          ]}
        >
          <Text style={styles.occupancyValue}>{occupancyValue}%</Text>
        </View>
        <Text style={styles.occupancyLabel}>OCCUPIED</Text>
        <View style={styles.lotDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Capacity:</Text>
            <Text style={styles.detailValue}>{capacityValue}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Occupied:</Text>
            <Text style={styles.detailValue}>{occupiedValue}</Text>
          </View>
        </View>
        {lastUpdated && (
          <Text style={styles.timestamp}>
            Last updated: {formatTimestamp(lastUpdated)}
          </Text>
        )}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#001E44',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    alignItems: 'center',
    gap: 16,
    margin: 8,
    minWidth: 160,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  lotName: {
    color: '#0B2141',
    fontSize: 20,
    fontWeight: '600',
    textAlign: 'center',
  },
  occupancyCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 8,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  occupancyValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#0B2141',
  },
  occupancyLabel: {
    color: '#0B2141',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.6,
  },
  lotDetails: {
    width: '100%',
    alignItems: 'center',
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    maxWidth: 200,
  },
  detailLabel: {
    color: '#0B2141',
    fontSize: 14,
    fontWeight: '500',
  },
  detailValue: {
    color: '#0B2141',
    fontSize: 14,
    fontWeight: '600',
  },
  timestamp: {
    color: '#0B2141',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
    opacity: 0.8,
  },
});

export default ParkingLotCard;
