import React, { useState } from 'react';
import { StyleSheet, View, Image, TouchableOpacity, Text, Dimensions, Modal, Pressable } from 'react-native';
import { COLORS, OCCUPANCY_THRESHOLDS } from '../constants';

const CampusMap = ({ parkingLots }) => {
  const [selectedLot, setSelectedLot] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const getLotData = (lotId) => {
    return parkingLots.find(lot => lot.lot === lotId) || null;
  };

  // Define parking lot zones with percentage-based coordinates
  // Percentages relative to the 1867x1294 image dimensions
  const parkingZones = [
    { lotId: 'G', xPercent: (580 / 1867) * 100, yPercent: (230 / 1294) * 100, widthPercent: (280 / 1867) * 100, heightPercent: (250 / 1294) * 100, label: 'Lot G' },
    { lotId: 'H', xPercent: (1000 / 1867) * 100, yPercent: (800 / 1294) * 100, widthPercent: (250 / 1867) * 100, heightPercent: (200 / 1294) * 100, label: 'Lot H' },
    { lotId: 'J', xPercent: (340 / 1867) * 100, yPercent: (870 / 1294) * 100, widthPercent: (150 / 1867) * 100, heightPercent: (120 / 1294) * 100, label: 'Lot J' },
    { lotId: 'M', xPercent: (710 / 1867) * 100, yPercent: (1000 / 1294) * 100, widthPercent: (150 / 1867) * 100, heightPercent: (120 / 1294) * 100, label: 'Lot M' },
  ];

  const handleZonePress = (zone) => {
    const lotData = getLotData(zone.lotId);
    setSelectedLot(lotData);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setSelectedLot(null);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Campus Parking Map</Text>
        <Text style={styles.headerSubtitle}>Tap parking areas to view occupancy</Text>
      </View>

      <View style={styles.mapWrapper}>
        <Image
          source={require('../assets/campus-map.png')}
          style={styles.campusMapImage}
          resizeMode="contain"
        />

        {/* Parking lot touchable zones */}
        <View style={styles.zonesOverlay}>
          {parkingZones.map((zone) => {
            const lotData = getLotData(zone.lotId);
            const occupancy = lotData?.occupancy || 0;

            return (
              <TouchableOpacity
                key={zone.lotId}
                style={[
                  styles.parkingZone,
                  {
                    left: `${zone.xPercent}%`,
                    top: `${zone.yPercent}%`,
                    width: `${zone.widthPercent}%`,
                    height: `${zone.heightPercent}%`,
                    borderColor: getOccupancyColor(occupancy),
                  },
                ]}
                onPress={() => handleZonePress(zone)}
                activeOpacity={0.7}
              />
            );
          })}
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={styles.legendTitle}>Occupancy Status</Text>
        <View style={styles.legendItems}>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: COLORS.GREEN }]} />
            <Text style={styles.legendText}>Open (≤{OCCUPANCY_THRESHOLDS.GREEN_MAX}%)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: COLORS.YELLOW }]} />
            <Text style={styles.legendText}>Busy ({OCCUPANCY_THRESHOLDS.GREEN_MAX + 1}–{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: COLORS.RED }]} />
            <Text style={styles.legendText}>Full (&gt;{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</Text>
          </View>
        </View>
      </View>

      {/* Modal for parking lot details */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <Pressable style={styles.modalOverlay} onPress={closeModal}>
          <Pressable style={styles.modalContent} onPress={(e) => e.stopPropagation()}>
            {selectedLot && (
              <>
                <Text style={styles.modalTitle}>Parking Lot {selectedLot.lot}</Text>
                <View style={styles.modalOccupancy}>
                  <View
                    style={[
                      styles.occupancyCircle,
                      { borderColor: getOccupancyColor(selectedLot.occupancy || 0) },
                    ]}
                  >
                    <Text style={styles.occupancyValue}>{selectedLot.occupancy || 0}%</Text>
                  </View>
                  <Text style={styles.occupancyLabel}>Occupied</Text>
                </View>
                <View style={styles.modalDetails}>
                  <Text style={styles.detailText}>
                    <Text style={styles.detailLabel}>Available:</Text> {selectedLot.occupiedSpaces !== undefined ? selectedLot.capacity - selectedLot.occupiedSpaces : 'N/A'}
                  </Text>
                  <Text style={styles.detailText}>
                    <Text style={styles.detailLabel}>Capacity:</Text> {selectedLot.capacity || 100}
                  </Text>
                  <Text style={styles.detailText}>
                    <Text style={styles.detailLabel}>Last Updated:</Text> {selectedLot.lastUpdated ? new Date(selectedLot.lastUpdated).toLocaleTimeString() : 'N/A'}
                  </Text>
                </View>
                <TouchableOpacity style={styles.closeButton} onPress={closeModal}>
                  <Text style={styles.closeButtonText}>Close</Text>
                </TouchableOpacity>
              </>
            )}
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f0f0',
  },
  header: {
    backgroundColor: COLORS.NITTANY_NAVY,
    paddingVertical: 20,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  headerTitle: {
    color: COLORS.WHITE,
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  headerSubtitle: {
    color: COLORS.WHITE,
    fontSize: 14,
    opacity: 0.9,
  },
  mapWrapper: {
    flex: 1,
    position: 'relative',
    padding: 10,
  },
  campusMapImage: {
    width: '100%',
    height: '100%',
  },
  zonesOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
  },
  parkingZone: {
    position: 'absolute',
    borderWidth: 3,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  legend: {
    backgroundColor: COLORS.WHITE,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.LIGHT_GRAY,
  },
  legendTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.NITTANY_NAVY,
    marginBottom: 12,
  },
  legendItems: {
    gap: 10,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendColor: {
    width: 20,
    height: 20,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 13,
    color: COLORS.TEXT,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: COLORS.WHITE,
    borderRadius: 16,
    padding: 24,
    width: '85%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.NITTANY_NAVY,
    marginBottom: 20,
    textAlign: 'center',
  },
  modalOccupancy: {
    alignItems: 'center',
    marginBottom: 20,
  },
  occupancyCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 5,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    marginBottom: 10,
  },
  occupancyValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.TEXT,
  },
  occupancyLabel: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  modalDetails: {
    borderTopWidth: 1,
    borderTopColor: COLORS.LIGHT_GRAY,
    paddingTop: 16,
    gap: 8,
  },
  detailText: {
    fontSize: 15,
    color: COLORS.TEXT,
    lineHeight: 22,
  },
  detailLabel: {
    fontWeight: '600',
    color: COLORS.NITTANY_NAVY,
  },
  closeButton: {
    marginTop: 20,
    backgroundColor: COLORS.BEAVER_BLUE,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: COLORS.WHITE,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CampusMap;
