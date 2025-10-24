import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, ScrollView, SafeAreaView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import ParkingLotCard from './components/ParkingLotCard';

export default function App() {
  const parkingLots = [
    { name: 'Parking Lot A', occupancy: 85 },
    { name: 'Parking Lot B', occupancy: 62 },
    { name: 'Parking Lot C', occupancy: 91 },
    { name: 'Parking Lot D', occupancy: 45 },
    { name: 'Parking Lot E', occupancy: 78 },
    { name: 'Parking Lot F', occupancy: 55 },
    { name: 'Parking Lot G', occupancy: 93 },
    { name: 'Parking Lot H', occupancy: 38 },
    { name: 'Parking Lot I', occupancy: 72 },
    { name: 'Parking Lot J', occupancy: 88 },
    { name: 'Parking Lot K', occupancy: 41 },
    { name: 'Parking Lot L', occupancy: 67 },
    { name: 'Parking Lot M', occupancy: 54 },
  ];

  return (
    <LinearGradient
      colors={['#667eea', '#764ba2']}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Campus Parking Status</Text>
        </View>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.parkingGrid}>
            {parkingLots.map((lot) => (
              <ParkingLotCard
                key={lot.name}
                lotName={lot.name}
                occupancy={lot.occupancy}
              />
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    paddingVertical: 20,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  headerTitle: {
    color: 'white',
    fontSize: 28,
    fontWeight: 'bold',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  parkingGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
  },
});
