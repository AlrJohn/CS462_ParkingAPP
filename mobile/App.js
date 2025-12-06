import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, SafeAreaView } from 'react-native';
import CampusMap from './components/CampusMap';

export default function App() {
  const parkingLots = [
    { lot: 'G', occupancy: 85, capacity: 100, occupiedSpaces: 85, lastUpdated: new Date() },
    { lot: 'H', occupancy: 62, capacity: 120, occupiedSpaces: 74, lastUpdated: new Date() },
    { lot: 'J', occupancy: 45, capacity: 80, occupiedSpaces: 36, lastUpdated: new Date() },
    { lot: 'M', occupancy: 54, capacity: 90, occupiedSpaces: 49, lastUpdated: new Date() },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <CampusMap parkingLots={parkingLots} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#001E44',
  },
});
