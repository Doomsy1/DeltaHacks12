import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { BASE_URL_BACKEND, BASE_URL_HEADLESS, BASE_URL_VIDEO } from './src/config';

export default function App() {
  const [healthStatus, setHealthStatus] = useState({
    backend: null,
    headless: null,
    video: null,
  });
  const [loading, setLoading] = useState(false);

  const checkHealth = async (serviceName, url) => {
    try {
      const response = await fetch(`${url}/health`);
      const data = await response.json();
      return { status: 'ok', data };
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    const [backendResult, headlessResult, videoResult] = await Promise.all([
      checkHealth('backend', BASE_URL_BACKEND),
      checkHealth('headless', BASE_URL_HEADLESS),
      checkHealth('video', BASE_URL_VIDEO),
    ]);

    setHealthStatus({
      backend: backendResult,
      headless: headlessResult,
      video: videoResult,
    });
    setLoading(false);
  };

  const getStatusColor = (status) => {
    if (!status) return '#999';
    return status.status === 'ok' ? '#4CAF50' : '#F44336';
  };

  const getStatusText = (status) => {
    if (!status) return 'Not checked';
    return status.status === 'ok' ? '✓ OK' : `✗ Error: ${status.error}`;
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>JobReels</Text>
      
      <View style={styles.statusContainer}>
        <View style={styles.serviceRow}>
          <Text style={styles.serviceLabel}>Backend:</Text>
          <View style={styles.statusBox}>
            <View style={[styles.statusIndicator, { backgroundColor: getStatusColor(healthStatus.backend) }]} />
            <Text style={styles.statusText}>{getStatusText(healthStatus.backend)}</Text>
          </View>
        </View>

        <View style={styles.serviceRow}>
          <Text style={styles.serviceLabel}>Headless:</Text>
          <View style={styles.statusBox}>
            <View style={[styles.statusIndicator, { backgroundColor: getStatusColor(healthStatus.headless) }]} />
            <Text style={styles.statusText}>{getStatusText(healthStatus.headless)}</Text>
          </View>
        </View>

        <View style={styles.serviceRow}>
          <Text style={styles.serviceLabel}>Video:</Text>
          <View style={styles.statusBox}>
            <View style={[styles.statusIndicator, { backgroundColor: getStatusColor(healthStatus.video) }]} />
            <Text style={styles.statusText}>{getStatusText(healthStatus.video)}</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity 
        style={[styles.button, loading && styles.buttonDisabled]} 
        onPress={handleRefresh}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Refresh</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 40,
    color: '#333',
  },
  statusContainer: {
    width: '100%',
    marginBottom: 30,
  },
  serviceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginBottom: 10,
  },
  serviceLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 16,
    color: '#333',
  },
  button: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 40,
    paddingVertical: 15,
    borderRadius: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
