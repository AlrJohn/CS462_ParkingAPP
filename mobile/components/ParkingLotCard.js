import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

function ParkingLotCard({ lotName, occupancy }) {
  const getOccupancyColor = (occupancy) => {
    if (occupancy >= 90) return '#ef4444';
    if (occupancy >= 70) return '#f59e0b';
    return '#22c55e';
  };

  return (
    <View style={styles.card}>
      <Text style={styles.lotName}>{lotName}</Text>
      <View
        style={[
          styles.occupancyCircle,
          { borderColor: getOccupancyColor(occupancy) }
        ]}
      >
        <Text style={styles.occupancyValue}>{occupancy}%</Text>
      </View>
      <Text style={styles.occupancyLabel}>OCCUPIED</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 4,
    alignItems: 'center',
    gap: 16,
    margin: 8,
    minWidth: 160,
  },
  lotName: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  occupancyCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 8,
    backgroundColor: '#f9fafb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  occupancyValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1f2937',
  },
  occupancyLabel: {
    color: '#6b7280',
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.8,
  },
});

export default ParkingLotCard;
