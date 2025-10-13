import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { api, ChatMessage, ChatRequest } from '../services/api';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load session history
    loadSessionHistory();
  }, [sessionId]);

  const loadSessionHistory = async () => {
    try {
      const history = await api.getSessionHistory(sessionId);
      setMessages(history);
    } catch (err) {
      console.error('Failed to load session history:', err);
      // Don't show error for empty history
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      content: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        message: inputMessage,
        session_id: sessionId,
      };

      const response = await api.sendMessage(request);
      
      const assistantMessage: ChatMessage = {
        content: response.response,
        sender: 'assistant',
        timestamp: response.timestamp,
        metadata: response.metadata,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please check your connection and try again.');
      
      const errorMessage: ChatMessage = {
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'assistant',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearSession = async () => {
    try {
      await api.clearSession(sessionId);
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Failed to clear session:', err);
      setError('Failed to clear session.');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" gutterBottom>
              AI Monitoring Assistant
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask questions about your system metrics, alerts, and performance
            </Typography>
          </Box>
          <IconButton 
            onClick={handleClearSession}
            color="secondary"
            title="Clear conversation"
          >
            <ClearIcon />
          </IconButton>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Messages area */}
      <Box 
        sx={{ 
          flexGrow: 1, 
          overflow: 'auto', 
          p: 1,
          backgroundColor: 'background.default',
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              p: 4,
            }}
          >
            <BotIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Welcome to AI Monitoring Agent
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Start a conversation about your system metrics and alerts. Here are some example queries:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {[
                'Show me CPU usage for all services',
                'What alerts are currently active?',
                'Check system health status',
                'Memory usage trends',
                'Network performance issues',
              ].map((example) => (
                <Chip
                  key={example}
                  label={example}
                  variant="outlined"
                  onClick={() => setInputMessage(example)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>
        ) : (
          <List sx={{ width: '100%' }}>
            {messages.map((message, index) => (
              <ListItem
                key={index}
                sx={{
                  display: 'flex',
                  flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                  mb: 2,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main',
                    mx: 1,
                  }}
                >
                  {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
                </Avatar>
                
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    backgroundColor: message.sender === 'user' 
                      ? 'primary.dark' 
                      : 'background.paper',
                  }}
                >
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {message.sender === 'user' ? 'You' : 'AI Assistant'} • {' '}
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ 
                    '& p': { margin: 0 },
                    '& pre': { 
                      backgroundColor: 'action.hover', 
                      p: 1, 
                      borderRadius: 1,
                      overflow: 'auto',
                    },
                    '& code': {
                      backgroundColor: 'action.hover',
                      px: 0.5,
                      borderRadius: 0.5,
                    },
                  }}>
                    {message.sender === 'assistant' ? (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    ) : (
                      <Typography>{message.content}</Typography>
                    )}
                  </Box>
                  
                  {message.metadata && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Processing time: {message.metadata.processing_time?.toFixed(2)}s
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </ListItem>
            ))}
            
            {isLoading && (
              <ListItem>
                <Avatar sx={{ bgcolor: 'secondary.main', mx: 1 }}>
                  <BotIcon />
                </Avatar>
                <Paper elevation={1} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CircularProgress size={20} />
                  <Typography color="text.secondary">AI Assistant is thinking...</Typography>
                </Paper>
              </ListItem>
            )}
          </List>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input area */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          display: 'flex',
          gap: 1,
          alignItems: 'flex-end',
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Ask about your system metrics, alerts, or performance..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          variant="outlined"
          size="small"
        />
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || isLoading}
          size="large"
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
};

export default ChatInterface;