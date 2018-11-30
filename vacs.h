/**
 * @file   periph/modem/protocols/vacs.h
 * @author Garrett L. Ward <wardgl@mymail.vcu.edu>
 * @date   Mon Jul  7 12:36:05 2014
 * 
 * @brief  Parser for low-level vacs routines. High-level vacs (read:
 * packet type definitions) do not belong here
 * 
 * 
 */

#ifndef VACS_H
#define VACS_H

#include <stdint.h>
#include <stdbool.h>

#include "comm/packet.h"


// VACS Packet Defines
#define SYNC_SIZE        2 /* SYNC0 + SYNC1 */
#define HEADER_SIZE      6 /* ADDR  + MSGID + LENGTH */
#define HEADER_TOTAL     (SYNC_SIZE + HEADER_SIZE)
#define CHECKSUM_SIZE    2 /* CHKA  + CHKB */
#define PAYLOAD_SIZE_MIN 0
#define PAYLOAD_SIZE_MAX 1024

#define PACKET_OVERHEAD (SYNC_SIZE + HEADER_SIZE + CHECKSUM_SIZE)
#define PACKET_SIZE_MAX (PACKET_OVERHEAD + PAYLOAD_SIZE_MAX)

#define SYNC0 0x76
#define SYNC1 0x63

#define SYNC0_INDEX      0
#define SYNC1_INDEX      1
#define DST_ADDR_INDEX   2
#define SRC_ADDR_INDEX   3
#define MSGID_LSB_INDEX  4
#define MSGID_MSB_INDEX  5
#define LENGTH_LSB_INDEX 6
#define LENGTH_MSB_INDEX 7
#define PAYLOAD_INDEX    8

#define CHK_A_OFFSET 8
#define CHK_B_OFFSET (CHK_A_OFFSET+1)

#define GCS_ADDRESS       0
#define FCS_ADDRESS       1
#define BROADCAST_ADDRESS 255


/** 
 * @struct VacsStats vacs.h "vacs/vacs.h"
 * @brief Statistics for the VACS parser
 */
typedef struct vacs_stats {
    uint32_t valid_packets;     /**< Valid packets */
    uint32_t parse_errors;      /**< Errored packed */
    uint32_t unhandled_packets; /**< Valid packets with no callback */
    uint32_t overruns;          /**< Packet overruns */
} VacsStats;

/** 
 * @struct VacsPacket vacs.h "periph/modem/protocols/vacs.h"
 * @brief A single VACS packet
 */
typedef struct vacs_packet {
    uint8_t src_addr;           /**< Source address of packet */
    uint8_t dest_addr;          /**< Destination address of packet */
    uint16_t m_id;              /**< Message ID of packet */
    uint16_t length;            /**< Length of data */
    uint8_t chk_a;              /**< Checksum byte A */
    uint8_t chk_b;              /**< Checksum byte B */
    uint8_t *data;              /**< Payload data (Unused) */
} VacsPacket;


/** 
 * @enum VACS_PARSER_STATE
 * @brief Possible states of the VACS parser
 * 
 */
typedef enum vacs_parser_state {
    VACS_PARSER_STATE_none,     /**< No bytes have been parsed */
    VACS_PARSER_STATE_sync0,    /**< Parsed SYNC0 */
    VACS_PARSER_STATE_sync1,
    VACS_PARSER_STATE_dst_addr,
    VACS_PARSER_STATE_src_addr,
    VACS_PARSER_STATE_msg_id_lsb,
    VACS_PARSER_STATE_msg_id_msb,
    VACS_PARSER_STATE_length_lsb,
    VACS_PARSER_STATE_length_msb,
    VACS_PARSER_STATE_data,     /**< Parsed data & read CHKA */
    VACS_PARSER_STATE_chka,     /**< Parsed data & read CHKB. do
                                 * validation and callback if
                                 * successful */
} VACS_PARSER_STATE;
 
/**
 * @struct VacsParser vacs.c "vacs/vacs.c"
 *
 * @brief VACS parser state 
 * 
 */
typedef struct vacs_parser {
    uint8_t buf[PAYLOAD_SIZE_MAX]; /**< Payload buffer */
    uint16_t packet_index;      /**< Index in buffer */
    uint8_t src_addr;           /**< Last parsed src address */
    uint8_t dest_addr;          /**< Last parsed dest address */
    uint16_t m_id;              /**< Last parsed message ID */
    uint16_t packet_length;     /**< Last parsed message length */
    uint8_t chk_a;              /**< Last parsed checksum A */
    uint8_t chk_b;              /**< Last parsed checksum B */
    bool packet_valid;          /**< True if last_packet is valid */
    VacsPacket last_packet;     /**< Last valid packet */
    VacsStats stats;            /**< Statistics for parser */
    VACS_PARSER_STATE state;    /**< State of parser*/
} VacsParser;

#define VACS_PARSER_INITIALIZER                 \
    {                                           \
    .buf = {0},                                 \
    .packet_index = 0,                          \
    .src_addr = 0,                              \
    .dest_addr = 0,                             \
    .m_id = 0,                                  \
    .packet_length = 0,                         \
    .chk_a = 0,                                 \
    .chk_b = 0,                                 \
    .packet_valid = false,                      \
    .last_packet = {0},                         \
    .stats = {0},                               \
    .state = VACS_PARSER_STATE_none,            \
    }
    


extern bool vacs_parse(VacsParser *parser, uint8_t *data, int length, int *parsed_length);
extern Packet *vacs_unpack(VacsParser *parser);
extern uint16_t vacs_pack(Packet *packet, uint8_t *buf);


#endif /* VACS_H */
