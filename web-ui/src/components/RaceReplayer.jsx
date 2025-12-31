import React, { useState, useEffect } from 'react';
import { Card, Button, Timeline, Space, Progress } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ForwardOutlined } from '@ant-design/icons';

const RaceReplayer = ({ raceData = null }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [raceProgress, setRaceProgress] = useState({});

  // サンプルレースデータ
  const sampleRace = {
    id: '20231230-01-01',
    datetime: '2023-12-30 12:30',
    stadium: '平和島',
    race_number: 1,
    racers: [
      { position: 1, name: '選手A', time: 65.2 },
      { position: 2, name: '選手B', time: 66.1 },
      { position: 3, name: '選手C', time: 66.5 },
      { position: 4, name: '選手D', time: 67.3 },
      { position: 5, name: '選手E', time: 68.1 },
      { position: 6, name: '選手F', time: 69.2 }
    ]
  };

  const race = raceData || sampleRace;
  const raceEvents = [
    { time: 0, text: 'スタート準備', type: 'info' },
    { time: 5, text: 'ピットアウト', type: 'info' },
    { time: 30, text: 'ターンマーク進入', type: 'warning' },
    { time: 45, text: '最終ターン', type: 'warning' },
    { time: 65, text: 'ゴール', type: 'success' }
  ];

  useEffect(() => {
    let interval;
    if (isPlaying && currentTime < 100) {
      interval = setInterval(() => {
        setCurrentTime(prev => Math.min(100, prev + 1 * playbackSpeed));
        updateRaceProgress(currentTime + 1 * playbackSpeed);
      }, 100);
    } else if (currentTime >= 100) {
      setIsPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentTime, playbackSpeed]);

  const updateRaceProgress = (time) => {
    const progress = {};
    race.racers.forEach((racer, index) => {
      const completion = Math.min(100, (time / 100) * 100);
      progress[racer.position] = completion;
    });
    setRaceProgress(progress);
  };

  const handlePlay = () => setIsPlaying(!isPlaying);
  const handleReset = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    setRaceProgress({});
  };
  const handleSpeedChange = (speed) => setPlaybackSpeed(speed);

  const getCurrentEvent = () => {
    const eventTime = (currentTime / 100) * 70; // 70秒レース
    return raceEvents.filter(event => event.time <= eventTime);
  };

  return (
    <Card 
      title={`レース再生: ${race.stadium} ${race.race_number}R`}
      extra={<span>{race.datetime}</span>}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 再生コントロール */}
        <Space>
          <Button 
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />} 
            onClick={handlePlay}
          >
            {isPlaying ? '一時停止' : '再生'}
          </Button>
          <Button icon={<ForwardOutlined />} onClick={handleReset}>
            リセット
          </Button>
          <Select 
            value={playbackSpeed} 
            onChange={handleSpeedChange}
            style={{ width: 100 }}
          >
            <Select.Option value={0.5}>0.5x</Select.Option>
            <Select.Option value={1}>1x</Select.Option>
            <Select.Option value={2}>2x</Select.Option>
            <Select.Option value={3}>3x</Select.Option>
          </Select>
        </Space>

        {/* 進捗バー */}
        <div>
          <Progress 
            percent={currentTime} 
            format={() => `${currentTime}%`}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>

        {/* レース進行タイムライン */}
        <Timeline>
          {getCurrentEvent().map((event, index) => (
            <Timeline.Item 
              key={index} 
              color={event.type === 'success' ? 'green' : event.type === 'warning' ? 'orange' : 'blue'}
            >
              {event.text}
            </Timeline.Item>
          ))}
        </Timeline>

        {/* 選手進捗 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {race.racers.map((racer) => (
            <div key={racer.position} style={{ textAlign: 'center' }}>
              <div>コース{racer.position}: {racer.name}</div>
              <Progress 
                percent={raceProgress[racer.position] || 0}
                size="small"
                format={() => ''}
              />
              <div style={{ fontSize: 12, color: '#666' }}>
                {racer.time}秒
              </div>
            </div>
          ))}
        </div>

        {/* 現在状況 */}
        <div style={{ padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
          <strong>現在の状況:</strong> {
            currentTime < 20 ? 'スタート准备中' :
            currentTime < 40 ? 'スタートダッシュチェック' :
            currentTime < 60 ? 'ターンマーク戦' :
            currentTime < 80 ? '最後の直線' :
            'ゴール'
          }
        </div>
      </Space>
    </Card>
  );
};

export default RaceReplayer;
