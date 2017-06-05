Message

<table>
  <tr>
    <td>Header</td>
    <td>Address</td>
    <td>Separator</td>
    <td>Message Body</td>
    <td>Terminator</td>
  </tr>
  <tr>
    <td>1 byte</td>
    <td>1-3 bytes</td>
    <td>1 byte</td>
    <td>N Bytes</td>
    <td>1 Byte</td>
  </tr>
</table>


<table>
  <tr>
    <td>Field</td>
    <td>Description</td>
    <td>Comment</td>
  </tr>
  <tr>
    <td>Header</td>
    <td>ASCII Character ":"</td>
    <td>Required</td>
  </tr>
  <tr>
    <td>Separator</td>
    <td>ASCII Character “Space”</td>
    <td>Optional</td>
  </tr>
  <tr>
    <td>Address</td>
    <td>1-3 bytes Address</td>
    <td>Optional</td>
  </tr>
  <tr>
    <td>Terminator</td>
    <td>CRLF carriage return and Line Feed (0x0D 0x0A
)</td>
    <td>Required</td>
  </tr>
</table>


Message Body

<table>
  <tr>
    <td>MNEMONIC</td>
    <td>SEPARATOR</td>
    <td>VALUES</td>
  </tr>
  <tr>
    <td>4 byte</td>
    <td>1 byte</td>
    <td>N bytes</td>
  </tr>
</table>


<table>
  <tr>
    <td>Field</td>
    <td>Description</td>
    <td>Comment</td>
  </tr>
  <tr>
    <td>Command (MNEMONIC)</td>
    <td>4 bytes key identifier</td>
    <td>Required</td>
  </tr>
  <tr>
    <td>Separator</td>
    <td>ASCII character ‘space’</td>
    <td>Optional</td>
  </tr>
  <tr>
    <td>Values</td>
    <td>N bytes value (max 6 bytes)</td>
    <td>Optional</td>
  </tr>
</table>


Acknowledge/Response

<table>
  <tr>
    <td>ACK </td>
    <td>ADDRESS</td>
    <td>SEP</td>
    <td>COMMAN</td>
    <td>SEP</td>
    <td>VALUE</td>
    <td>TERM</td>
  </tr>
  <tr>
    <td>1 byte</td>
    <td>3 bytes</td>
    <td>1 byte</td>
    <td>4 bytes</td>
    <td>1 byte</td>
    <td>6 bytes</td>
    <td>1 byte</td>
  </tr>
</table>


<table>
  <tr>
    <td>Field</td>
    <td>Description</td>
    <td>Comment</td>
  </tr>
  <tr>
    <td>ACK</td>
    <td>ASCII character ‘%’</td>
    <td>Always</td>
  </tr>
  <tr>
    <td>SEP</td>
    <td>ASCII character ‘ space’</td>
    <td>Always</td>
  </tr>
  <tr>
    <td>VALUE</td>
    <td>6 bytes return value</td>
    <td>Always</td>
  </tr>
  <tr>
    <td>TERM</td>
    <td>CRLF (0x0D 0x0A)</td>
    <td>Always</td>
  </tr>
</table>


Different Commands

<table>
  <tr>
    <td>Command (MNEMONIC)</td>
    <td>Explanation</td>
    <td></td>
  </tr>
  <tr>
    <td>POWR (POWR)</td>
    <td>Turns RaspBerry Pi in Camera trap on or off</td>
    <td></td>
  </tr>
  <tr>
    <td>IDENTIFY (IDEN)</td>
    <td>Ask the RaspBerry Pi in Camera trap to identify itself</td>
    <td></td>
  </tr>
  <tr>
    <td>Reset (RSET)</td>
    <td>Reset camera trap</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</table>


