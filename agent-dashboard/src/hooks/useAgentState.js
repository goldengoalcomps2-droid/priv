/**
 * useAgentState() - Core hook for agent team state management.
 *
 * Replace the mock simulation with real WebSocket/API data by
 * modifying the `simulateTick` function or replacing setInterval
 * with a WebSocket listener.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { AGENTS, TASKS, COLLAB_PAIRS } from '../data/agents';

const STATES = ['idle', 'working', 'collaborating', 'waiting', 'complete'];

function randomTask(agentId) {
  const pool = TASKS[agentId] || TASKS.default;
  return pool[Math.floor(Math.random() * pool.length)];
}

function createInitialState() {
  return AGENTS.map(a => ({
    ...a,
    state: 'idle',
    task: null,
    taskStartedAt: null,
    collaboratingWith: null,
    completedCount: 0,
  }));
}

function createLogEntry(agent, state, task) {
  const msgs = {
    idle: `${agent.name} is now idle`,
    working: `${agent.name} started: ${task}`,
    collaborating: `${agent.name} collaborating on: ${task}`,
    waiting: `${agent.name} waiting for input`,
    complete: `${agent.name} completed: ${task}`,
  };
  return {
    id: Date.now() + Math.random(),
    timestamp: new Date(),
    agent: agent.id,
    agentName: agent.name,
    color: agent.color,
    message: msgs[state] || `${agent.name}: ${state}`,
    type: state,
  };
}

export function useAgentState(tickInterval = 3000) {
  const [agents, setAgents] = useState(createInitialState);
  const [log, setLog] = useState([]);
  const [cycle, setCycle] = useState(0);
  const tickRef = useRef(null);

  const addLog = useCallback((entry) => {
    setLog(prev => [entry, ...prev].slice(0, 50));
  }, []);

  const simulateTick = useCallback(() => {
    setCycle(c => c + 1);

    setAgents(prev => {
      const next = prev.map(a => ({ ...a }));

      // Clear collaborations
      next.forEach(a => { a.collaboratingWith = null; });

      // Random state transitions
      const changeCount = Math.floor(Math.random() * 3) + 1;
      const indices = [];
      while (indices.length < changeCount) {
        const idx = Math.floor(Math.random() * next.length);
        if (!indices.includes(idx)) indices.push(idx);
      }

      for (const idx of indices) {
        const agent = next[idx];
        const oldState = agent.state;

        // State machine logic
        if (oldState === 'idle') {
          const roll = Math.random();
          if (roll < 0.5) {
            agent.state = 'working';
            agent.task = randomTask(agent.id);
            agent.taskStartedAt = Date.now();
          } else if (roll < 0.7) {
            agent.state = 'waiting';
            agent.task = 'Awaiting approval';
            agent.taskStartedAt = Date.now();
          }
        } else if (oldState === 'working') {
          const roll = Math.random();
          if (roll < 0.3) {
            agent.state = 'complete';
            agent.completedCount++;
          } else if (roll < 0.45) {
            agent.state = 'collaborating';
            // Pick a collaboration partner
            const pair = COLLAB_PAIRS.find(p => p.includes(agent.id));
            if (pair) {
              const partnerId = pair.find(id => id !== agent.id);
              agent.collaboratingWith = partnerId;
              const partner = next.find(a => a.id === partnerId);
              if (partner) {
                partner.state = 'collaborating';
                partner.collaboratingWith = agent.id;
                partner.task = agent.task;
                partner.taskStartedAt = agent.taskStartedAt;
              }
            }
          }
        } else if (oldState === 'collaborating') {
          if (Math.random() < 0.4) {
            agent.state = 'complete';
            agent.completedCount++;
            agent.collaboratingWith = null;
          }
        } else if (oldState === 'waiting') {
          if (Math.random() < 0.5) {
            agent.state = 'working';
            agent.task = randomTask(agent.id);
            agent.taskStartedAt = Date.now();
          }
        } else if (oldState === 'complete') {
          agent.state = 'idle';
          agent.task = null;
          agent.taskStartedAt = null;
        }

        if (agent.state !== oldState) {
          // Defer log entry
          setTimeout(() => {
            addLog(createLogEntry(agent, agent.state, agent.task));
          }, 0);
        }
      }

      return next;
    });
  }, [addLog]);

  useEffect(() => {
    // Initial burst
    setTimeout(simulateTick, 500);
    tickRef.current = setInterval(simulateTick, tickInterval);
    return () => clearInterval(tickRef.current);
  }, [simulateTick, tickInterval]);

  // Get active collaborations as pairs
  const collaborations = agents
    .filter(a => a.state === 'collaborating' && a.collaboratingWith)
    .reduce((pairs, a) => {
      const existing = pairs.find(
        p => (p[0] === a.id && p[1] === a.collaboratingWith) ||
             (p[1] === a.id && p[0] === a.collaboratingWith)
      );
      if (!existing) pairs.push([a.id, a.collaboratingWith]);
      return pairs;
    }, []);

  return { agents, log, cycle, collaborations };
}
