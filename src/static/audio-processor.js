class AudioRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffers = [];
        this.isRecording = false;
        this.sampleCounter = 0;
        this.CHUNK_SIZE = 16000; // Process 1 second of audio at 16kHz
        
        this.port.onmessage = (event) => {
            if (event.data.command === 'start') {
                this.isRecording = true;
                this.buffers = [];
                this.sampleCounter = 0;
            } else if (event.data.command === 'stop') {
                this.isRecording = false;
                // Send any remaining buffered audio
                if (this.buffers.length > 0) {
                    this.sendBufferedAudio();
                }
                this.buffers = [];
                this.sampleCounter = 0;
            }
        };
    }

    sendBufferedAudio() {
        const totalLength = this.buffers.reduce((sum, buf) => sum + buf.length, 0);
        const concatenated = new Float32Array(totalLength);
        let offset = 0;
        for (const buffer of this.buffers) {
            concatenated.set(buffer, offset);
            offset += buffer.length;
        }
        this.port.postMessage({
            type: 'audio-chunk',
            audioData: concatenated
        });
        this.buffers = [];
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input.length > 0 && this.isRecording) {
            const audioData = new Float32Array(input[0]);
            this.buffers.push(audioData);
            this.sampleCounter += audioData.length;
            
            // Send chunk when we've accumulated enough samples
            if (this.sampleCounter >= this.CHUNK_SIZE) {
                this.sendBufferedAudio();
                this.sampleCounter = 0;
            }
            
            this.port.postMessage({ 
                type: 'buffer-update',
                samplesRecorded: this.sampleCounter
            });
        }
        return true;
    }
}

registerProcessor('audio-recorder-processor', AudioRecorderProcessor);