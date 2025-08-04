import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import Voice from '@react-native-voice/voice';
import ApiService from '../services/ApiService';

const HomeScreen = () => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    ApiService.initialize();
    
    Voice.onSpeechStart = () => setIsListening(true);
    Voice.onSpeechEnd = () => setIsListening(false);
    Voice.onSpeechResults = (event) => {
      setQuestion(event.value[0]);
    };
    Voice.onSpeechError = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const handleQuery = async () => {
    if (!question.trim()) return;

    setLoading(true);
    try {
      const result = await ApiService.query(question);
      setResponse(result.content);
    } catch (error) {
      setResponse('Error: Unable to get response');
    } finally {
      setLoading(false);
    }
  };

  const startListening = async () => {
    try {
      await Voice.start('en-US');
    } catch (error) {
      console.error('Error starting voice recognition:', error);
    }
  };

  const stopListening = async () => {
    try {
      await Voice.stop();
    } catch (error) {
      console.error('Error stopping voice recognition:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Open LLM Assistant</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Ask a coding question..."
        value={question}
        onChangeText={setQuestion}
        multiline
      />

      <View style={styles.buttonContainer}>
        <Button
          title={isListening ? 'Stop Listening' : '🎤 Voice Input'}
          onPress={isListening ? stopListening : startListening}
          color={isListening ? '#ff4444' : '#007AFF'}
        />
        
        <Button
          title="Get Answer"
          onPress={handleQuery}
          disabled={loading || !question.trim()}
        />
      </View>

      {loading && (
        <ActivityIndicator size="large" color="#007AFF" style={styles.loader} />
      )}

      {response ? (
        <View style={styles.responseContainer}>
          <Text style={styles.responseTitle}>Response:</Text>
          <Text style={styles.responseText}>{response}</Text>
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  input: {
    height: 100,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 20,
    backgroundColor: 'white',
    fontSize: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  loader: {
    marginVertical: 20,
  },
  responseContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  responseTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  responseText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#666',
  },
});

export default HomeScreen;