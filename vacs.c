
#include "vacs.h"

#include <stdlib.h> // NULL
#include <string.h> // memcpy()


/** 
 * @brief Parse up to \p length bytes of data, stopping when a
 * complete valid VACS packet has been found
 *
 * This will stop when a valid packet has been found; proper use of
 * the function will require repeatedly calling vacs_parse until
 * length == parsed_length, while handling any packets which are
 * successfully parsed in the mean time. 
 * 
 * @param parser VacsParser instance to use
 * @param data Data to parse
 * @param length Length of \p data
 * @param parsed_length Pointer to location to store actual parsed
 * length in
 * 
 * @return true if a packet was parsed, false otherwise
 */
bool vacs_parse(VacsParser *parser, uint8_t *data, int length, int *parsed_length) {
    int i;
    bool valid_packet = false;
    for (i = 0; i < length; i++) {
        switch(parser->state) {
            case VACS_PARSER_STATE_sync0:
                if (SYNC1 == data[i]) {
                    parser->chk_a = 0;
                    parser->chk_b = 0;
                    parser->state = VACS_PARSER_STATE_sync1;
                } else {
                    parser->stats.parse_errors++;
                    parser->state = VACS_PARSER_STATE_none;
                }
                break;

            case VACS_PARSER_STATE_sync1:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->dest_addr = data[i];
                parser->state = VACS_PARSER_STATE_dst_addr;
                break;

            case VACS_PARSER_STATE_dst_addr:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->src_addr = data[i];
                parser->state = VACS_PARSER_STATE_src_addr;
                break;

            case VACS_PARSER_STATE_src_addr:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->m_id = data[i];
                parser->state = VACS_PARSER_STATE_msg_id_lsb;
                break;
               
            case VACS_PARSER_STATE_msg_id_lsb:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->m_id += (data[i] << 8);
                parser->state = VACS_PARSER_STATE_msg_id_msb;
                break;

            case VACS_PARSER_STATE_msg_id_msb:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->packet_length = data[i];
                parser->state = VACS_PARSER_STATE_length_lsb;
                break;

            case VACS_PARSER_STATE_length_lsb:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->packet_length += (data[i] << 8);
                if (parser->packet_length >= PAYLOAD_SIZE_MAX) {
                    parser->stats.parse_errors++;
                    parser->state = VACS_PARSER_STATE_none;
                } else if (parser->packet_length == 0) {
                    parser->state = VACS_PARSER_STATE_data;
                } else {
                    parser->state = VACS_PARSER_STATE_length_msb;
                    parser->packet_index = 0;
                    // If we get this far into another packet without
                    // the last packet being copied out, it's no
                    // longer valid since the next byte we get will
                    // overwrite the payload
                    if (parser->packet_valid) {
                        parser->stats.overruns += 1;
                        parser->packet_valid = false;
                    }
                }
                break;

            case VACS_PARSER_STATE_length_msb:
                parser->chk_a += data[i];
                parser->chk_b += parser->chk_a;
                parser->buf[parser->packet_index] = data[i];
                parser->packet_index += 1;
                if (parser->packet_index >= parser->packet_length) {
                    parser->state = VACS_PARSER_STATE_data;
                }
                break;
              
            case VACS_PARSER_STATE_data:
                if (parser->chk_a == data[i]) {
                    parser->state = VACS_PARSER_STATE_chka;
                } else {
                    parser->stats.parse_errors++;
                    parser->state = VACS_PARSER_STATE_none;
                }
                break;

            case VACS_PARSER_STATE_chka:
                // Regardless of what happens, reset the parser
                parser->state = VACS_PARSER_STATE_none;
                if (parser->chk_b == data[i]) {
                    // Valid packets ahoy
                    parser->last_packet.src_addr = parser->src_addr;
                    parser->last_packet.dest_addr = parser->dest_addr;
                    parser->last_packet.m_id = parser->m_id;
                    parser->last_packet.length = parser->packet_length;
                    parser->last_packet.chk_a = parser->chk_a;
                    parser->last_packet.chk_b = parser->chk_b;
                    parser->packet_valid = true;
                    parser->stats.valid_packets += 1;
                    valid_packet = true;
                    goto cleanup;
                } else {
                    parser->stats.parse_errors++;
                }
                break;

            case VACS_PARSER_STATE_none:
            default:
                if (SYNC0 == data[i]) {
                    parser->state = VACS_PARSER_STATE_sync0; 
                }
                break;
        }
    }

cleanup:
    *parsed_length = i;
    return valid_packet;
}

Packet *vacs_unpack(VacsParser *parser) {
    if (!parser || !parser->packet_valid) {
        return NULL;
    }

    Packet *packet = packet_new();

    if (packet) {
        packet->src_addr = parser->last_packet.src_addr;
        packet->dest_addr = parser->last_packet.dest_addr;
        packet->id = parser->last_packet.m_id;
        packet->length = parser->last_packet.length;
        if (packet->length >= COMM_MAX_PACKET_DATA_SIZE) {
            // Can't fit, free packet and exit
            packet_free(&packet);
            goto cleanup;
        }
        memcpy(packet->data, parser->buf, packet->length);
    }
        
    cleanup:
    return packet;
}

    

/** 
 * @brief Pack data into a valid VACS packet
 *
 * @param packet Generic packet to pack
 * @param buf destination buffer for new packet
 * 
 * @return total size of new packet, including header and checksum. a
 * value less than \p length + 10 means the packing failed.
 * 
 */
uint16_t vacs_pack(Packet *packet, uint8_t *buf) {
    uint8_t chk_a = 0, chk_b = 0;
    uint16_t i;
    buf[SYNC0_INDEX] = SYNC0;
    buf[SYNC1_INDEX] = SYNC1;
    // Dest addr
    buf[DST_ADDR_INDEX] = (uint8_t)packet->dest_addr;
    chk_a += buf[DST_ADDR_INDEX];
    chk_b += chk_a;

    // Src addr
    buf[SRC_ADDR_INDEX] = (uint8_t)packet->src_addr;
    chk_a += buf[SRC_ADDR_INDEX];
    chk_b += chk_a;

    // Message LSB & MSB
    buf[MSGID_LSB_INDEX] = (packet->id & 0xFF);
    chk_a += buf[MSGID_LSB_INDEX];
    chk_b += chk_a;
    buf[MSGID_MSB_INDEX] = ((packet->id & 0xFF00) >> 8);
    chk_a += buf[MSGID_MSB_INDEX];
    chk_b += chk_a;

    // Length LSB & MSB
    buf[LENGTH_LSB_INDEX] = (packet->length & 0xFF);
    chk_a += buf[LENGTH_LSB_INDEX];
    chk_b += chk_a;
    buf[LENGTH_MSB_INDEX] = ((packet->length & 0xFF00) >> 8);
    chk_a += buf[LENGTH_MSB_INDEX];
    chk_b += chk_a;

    // Payload
    for (i = PAYLOAD_INDEX; i < PAYLOAD_INDEX + packet->length; i++) {
        buf[i] = packet->data[i - PAYLOAD_INDEX]; 
        chk_a += buf[i];
        chk_b += chk_a;
    }

    // Checksum
    buf[i++] = chk_a;
    buf[i++] = chk_b;

    if (i != (packet->length + PACKET_OVERHEAD)) {
        #ifdef DEBUG
        /* uprintf("You're bad at math, eh? Got actual length %lu instead of %lu\r\n", i, length+10); */
        #endif
        return 0;
    }
    return i;
}
