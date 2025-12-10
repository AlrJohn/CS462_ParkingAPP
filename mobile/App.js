import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, SafeAreaView, ActivityIndicator, View, Text } from 'react-native';
import CampusMap from './components/CampusMap';
import { COLORS } from './constants';

const API_URL = 'https://cs462-parkingapp.onrender.com/getLotCount';
const API_KEY = '123';

export default function App() {
  const [parkingLots, setParkingLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchParkingData = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Raw API response:', data);

      // Transform API data to match the expected format
      const formattedData = data.map(item => ({
        lot: item.lot,
        occupancy: item.occupancy,
        capacity: item.capacity,
        occupiedSpaces: item.occupiedSpaces,
        lastUpdated: new Date(item.lastUpdated || new Date()),
      }));

      console.log('Formatted parking data:', formattedData);
      setParkingLots(formattedData);
      setError(null);
    } catch (err) {
      console.error('Error fetching parking data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParkingData();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchParkingData, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={COLORS.WHITE} />
          <Text style={styles.loadingText}>Loading parking data...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centerContainer}>
          <Text style={styles.errorText}>Error: {error}</Text>
          <Text style={styles.errorSubtext}>Please check your connection</Text>
        </View>
      </SafeAreaView>
    );
  }

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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: COLORS.WHITE,
    fontSize: 16,
    marginTop: 16,
  },
  errorText: {
    color: COLORS.RED,
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  errorSubtext: {
    color: COLORS.WHITE,
    fontSize: 14,
    textAlign: 'center',
  },
});
