import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class ApiService {
  constructor() {
    this.baseURL = 'http://localhost:8000';
    this.token = null;
  }

  async initialize() {
    // Load saved configuration
    const savedConfig = await AsyncStorage.getItem('openllm_config');
    if (savedConfig) {
      const config = JSON.parse(savedConfig);
      this.baseURL = config.apiURL || this.baseURL;
      this.token = config.apiToken;
    }
  }

  async saveConfig(apiURL, apiToken) {
    const config = { apiURL, apiToken };
    await AsyncStorage.setItem('openllm_config', JSON.stringify(config));
    this.baseURL = apiURL;
    this.token = apiToken;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    try {
      const response = await axios({ url, headers, ...options });
      return response.data;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  async query(question, language = 'python') {
    return this.request('/process', {
      method: 'POST',
      data: {
        content: question,
        metadata: {
          language,
          source: 'mobile',
        },
      },
    });
  }

  async analyzeCode(code, language, analysisType = 'refactor') {
    return this.request('/process', {
      method: 'POST',
      data: {
        content: `Analyze this ${language} code for ${analysisType} improvements`,
        context: {
          code,
          language,
          analysisType,
        },
        metadata: {
          source: 'mobile',
          analysisType,
        },
      },
    });
  }

  async createSession(name, code, language, isPublic = false) {
    return this.request('/collaboration/sessions', {
      method: 'POST',
      data: {
        name,
        code,
        language,
        is_public: isPublic,
      },
    });
  }

  async getVersions() {
    return this.request('/versions');
  }

  async createVersion(description, author = 'mobile') {
    return this.request('/versions', {
      method: 'POST',
      data: {
        description,
        author,
      },
    });
  }
}

export default new ApiService();