class CryptoService {
    static CRYPTO_KEY = 'valorant-transport-ranks-v1';
    static IV_LENGTH = 12;

    static async getKey() {
        const encoder = new TextEncoder();
        const salt = encoder.encode('valorant-static-salt');
        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            encoder.encode(this.CRYPTO_KEY),
            'PBKDF2',
            false,
            ['deriveBits', 'deriveKey']
        );

        return await crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: 100000,
                hash: 'SHA-256'
            },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt', 'decrypt']
        );
    }

    static async encrypt(text) {
        try {
            if (!text) throw new Error('Dados vazios');
            
            const key = await this.getKey();
            const encoder = new TextEncoder();
            const iv = crypto.getRandomValues(new Uint8Array(this.IV_LENGTH));
            const dataBuffer = encoder.encode(text);

            const encrypted = await crypto.subtle.encrypt(
                { name: 'AES-GCM', iv },
                key,
                dataBuffer
            );

            // Combina IV + dados criptografados
            const encryptedArray = new Uint8Array(iv.length + encrypted.byteLength);
            encryptedArray.set(iv);
            encryptedArray.set(new Uint8Array(encrypted), iv.length);

            // Converte para base64 usando btoa
            return btoa(String.fromCharCode.apply(null, encryptedArray));
        } catch (error) {
            console.error('Erro na criptografia:', error);
            throw error;
        }
    }

    static async decrypt(encryptedBase64) {
        try {
            if (!encryptedBase64) throw new Error('Dados vazios');

            const key = await this.getKey();
            const decoder = new TextDecoder();
            
            // Converte base64 para array de bytes
            const encryptedArray = new Uint8Array(
                atob(encryptedBase64).split('').map(c => c.charCodeAt(0))
            );

            if (encryptedArray.length <= this.IV_LENGTH) {
                throw new Error('Dados criptografados inválidos');
            }

            const iv = encryptedArray.slice(0, this.IV_LENGTH);
            const ciphertext = encryptedArray.slice(this.IV_LENGTH);

            const decrypted = await crypto.subtle.decrypt(
                { name: 'AES-GCM', iv },
                key,
                ciphertext
            );

            return decoder.decode(decrypted);
        } catch (error) {
            console.error('Erro na descriptografia:', error);
            throw error;
        }
    }
}
