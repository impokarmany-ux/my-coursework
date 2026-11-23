public class WatcherHeader // TypeDefIndex: 60695
{
	// Fields
	public static readonly int MinSize; // 0x0
	public static readonly uint HashSeed; // 0x4
	public uint Chksum; // 0x10
	public uint CodecAndSize; // 0x14
	private byte Flags; // 0x18
	public uint ComFlagsAndMsgId; // 0x1C
	public byte MulticastN; // 0x20
	public uint N32; // 0x24
	public ulong N64; // 0x28
	public uint ReqId; // 0x30
	public ushort Warden; // 0x34

	// Properties
	public uint MsgId { get; set; }
	public uint ComFlag { get; set; }
	public int PayloadSize { get; set; }
	public byte Codec { get; set; }

	// Methods

	// RVA: 0x1493BBDC Offset: 0x14937BDC VA: 0x1493BBDC
	public static uint GetHeaderSize(uint comFlagsAndMsgID) { }

	// RVA: 0x1493B650 Offset: 0x14937650 VA: 0x1493B650
	public uint get_MsgId() { }

	// RVA: 0x14939D1C Offset: 0x14935D1C VA: 0x14939D1C
	public void set_MsgId(uint value) { }

	// RVA: 0x1493B6B8 Offset: 0x149376B8 VA: 0x1493B6B8
	public uint get_ComFlag() { }

	// RVA: 0x14939E14 Offset: 0x14935E14 VA: 0x14939E14
	public void set_ComFlag(uint value) { }

	// RVA: 0x1493C228 Offset: 0x14938228 VA: 0x1493C228
	public int get_PayloadSize() { }

	// RVA: 0x1493C37C Offset: 0x1493837C VA: 0x1493C37C
	public void set_PayloadSize(int value) { }

	// RVA: 0x1493FF48 Offset: 0x1493BF48 VA: 0x1493FF48
	public byte get_Codec() { }

	// RVA: 0x14939D9C Offset: 0x14935D9C VA: 0x14939D9C
	public void set_Codec(byte value) { }

	// RVA: 0x1493FFAC Offset: 0x1493BFAC VA: 0x1493FFAC
	public static void Serialize(Stream s, WatcherHeader h) { }

	// RVA: 0x1493C070 Offset: 0x14938070 VA: 0x1493C070
	public static WatcherHeader Deserialize(Stream s) { }

	// RVA: 0x1494013C Offset: 0x1493C13C VA: 0x1494013C Slot: 3
	public override string ToString() { }

	// RVA: 0x14939CA4 Offset: 0x14935CA4 VA: 0x14939CA4
	public void .ctor() { }

	// RVA: 0x149405AC Offset: 0x1493C5AC VA: 0x149405AC
	private static void .cctor() { }
}
